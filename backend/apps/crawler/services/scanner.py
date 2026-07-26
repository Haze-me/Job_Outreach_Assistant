"""Scan orchestration.

``start_scan`` is called from the request cycle: it validates, records a
pending scan, and hands off. ``run_scan`` is what the Celery worker executes.
Keeping them separate is what lets the same code run inline (eager mode) or on
a worker without branching.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.common.exceptions import ConflictError, ServiceError
from apps.crawler.models import Page, PageType, Scan, ScanStatus
from apps.crawler.services.discovery import (
    TYPE_PRIORITY,
    Candidate,
    classify_page_type,
    discover_links,
    extract_title,
    probe_candidates,
)
from apps.crawler.services.extraction import extract_emails
from apps.crawler.services.http import FetchError, SafeHttpClient, UnsafeUrlError, assert_safe_url
from apps.crawler.services.sitemap import discover_sitemap_urls

if TYPE_CHECKING:  # pragma: no cover
    from apps.companies.models import Company

logger = logging.getLogger(__name__)


class ScanAlreadyRunningError(ConflictError):
    default_detail = "A scan is already running for this company."
    default_code = "scan_already_running"


class InvalidScanTargetError(ServiceError):
    default_detail = "This company's website cannot be scanned."
    default_code = "invalid_scan_target"


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------
def start_scan(*, user, company: Company) -> Scan:
    """Records a pending scan and queues it.

    The URL is validated *before* the scan row is created, so an unscannable
    website fails immediately with a clear error instead of producing a scan
    that is destined to fail asynchronously.
    """
    try:
        assert_safe_url(company.website)
    except UnsafeUrlError as exc:
        raise InvalidScanTargetError(str(exc)) from exc

    if Scan.objects.filter(
        company=company, status__in=[ScanStatus.PENDING, ScanStatus.RUNNING]
    ).exists():
        raise ScanAlreadyRunningError()

    scan = Scan.objects.create(user=user, company=company, target_url=company.website)

    # Queue only once the surrounding transaction commits. Without this the
    # worker can pick up the job before the row it needs is visible -- a race
    # that only shows up under load, which is the worst kind.
    transaction.on_commit(lambda: _dispatch(scan.pk))
    logger.info("Queued scan %s for company %s", scan.pk, company.pk)
    return scan


def _dispatch(scan_id) -> None:
    from apps.crawler.tasks import run_company_scan

    result = run_company_scan.delay(str(scan_id))
    task_id = getattr(result, "id", "") or ""
    Scan.objects.filter(pk=scan_id).update(task_id=task_id)


def run_scan(*, scan_id) -> Scan:
    """Executes a scan end to end. Never raises for crawl failures.

    A site being unreachable is an expected outcome, not a bug: it is recorded
    on the scan as ``failed`` with a message the user can read.
    """
    scan = Scan.objects.select_related("company", "user").get(pk=scan_id)

    if scan.status != ScanStatus.PENDING:
        # Guards against a task delivered twice.
        logger.info("Scan %s is already %s; skipping", scan.pk, scan.status)
        return scan

    scan.status = ScanStatus.RUNNING
    scan.started_at = timezone.now()
    scan.save(update_fields=["status", "started_at", "updated_at"])

    try:
        _crawl(scan)
        scan.status = ScanStatus.COMPLETED
        scan.error_message = ""
    except Exception as exc:  # noqa: BLE001 - the failure belongs on the record
        logger.exception("Scan %s failed", scan.pk)
        scan.status = ScanStatus.FAILED
        scan.error_message = str(exc)[:1000]

    scan.finished_at = timezone.now()
    scan.save(
        update_fields=[
            "status",
            "error_message",
            "finished_at",
            "pages_discovered",
            "pages_scanned",
            "contacts_found",
            "updated_at",
        ]
    )
    logger.info(
        "Scan %s finished: %s pages, %s contacts (%s)",
        scan.pk,
        scan.pages_scanned,
        scan.contacts_found,
        scan.status,
    )
    return scan


# ---------------------------------------------------------------------------
# The crawl itself
# ---------------------------------------------------------------------------
def _crawl(scan: Scan) -> None:
    root_url = scan.target_url
    max_pages = settings.CRAWLER_MAX_PAGES
    max_depth = settings.CRAWLER_MAX_DEPTH

    # Priority queue kept sorted by (priority, depth): recruitment pages are
    # visited before generic ones, shallow before deep.
    queue: list[Candidate] = [
        Candidate(priority=-1, depth=0, url=root_url, page_type=PageType.HOME)
    ]
    queued_urls: set[str] = {root_url}
    visited: set[str] = set()

    scan.pages_discovered = 1
    scan.save(update_fields=["pages_discovered", "updated_at"])

    with SafeHttpClient() as client:
        # The homepage must be reachable; if it is not, the scan has failed.
        # Every other page is best-effort.
        first = True
        seeded = False
        # Counts pages actually recorded, so probes for URLs that turn out not
        # to exist do not eat the budget.
        scanned = 0

        while queue and scanned < max_pages:
            queue.sort()
            candidate = queue.pop(0)
            if candidate.url in visited:
                continue
            visited.add(candidate.url)

            if not client.robots.is_allowed(candidate.url):
                logger.info("robots.txt disallows %s", candidate.url)
                continue

            try:
                result = client.get_html(candidate.url)
            except (FetchError, UnsafeUrlError) as exc:
                if first:
                    raise
                if candidate.speculative:
                    # A guessed URL that 404s is an expected outcome, not a
                    # failure worth putting in the scan report.
                    logger.debug("Probe missed %s", candidate.url)
                    queued_urls.discard(candidate.url)
                    scan.pages_discovered = len(queued_urls)
                    continue
                logger.info("Skipping %s: %s", candidate.url, exc)
                _record_page(scan, candidate, status_code=None, title="", emails_found=0)
                scanned += 1
                _bump_scanned(scan)
                continue
            finally:
                first = False

            emails = extract_emails(result.html)
            page = _record_page(
                scan,
                candidate,
                status_code=result.status_code,
                title=extract_title(result.html),
                emails_found=len(emails),
                final_url=result.url,
            )

            if emails:
                scan.contacts_found += _save_contacts(scan=scan, page=page, emails=emails)

            if candidate.depth < max_depth:
                _enqueue_links(
                    html=result.html,
                    base_url=result.url,
                    root_url=root_url,
                    depth=candidate.depth + 1,
                    queue=queue,
                    queued_urls=queued_urls,
                    budget=max_pages,
                )

            # After the homepage, top the queue up from sources that do not
            # depend on HTML links existing at all.
            if not seeded:
                seeded = True
                _seed_from_sitemap_and_probes(
                    client=client,
                    root_url=root_url,
                    queue=queue,
                    queued_urls=queued_urls,
                    budget=max_pages,
                )

            scan.pages_discovered = len(queued_urls)
            scanned += 1
            _bump_scanned(scan)


def _enqueue_links(
    *,
    html: str,
    base_url: str,
    root_url: str,
    depth: int,
    queue: list[Candidate],
    queued_urls: set[str],
    budget: int,
) -> None:
    for link in discover_links(html, base_url, root_url, depth=depth):
        if link.url in queued_urls:
            continue
        # Discovering thousands of links on a large site would make the
        # progress figure meaningless; stop once the budget is covered.
        if len(queued_urls) >= budget * 2:
            break
        queued_urls.add(link.url)
        queue.append(link)


def _seed_from_sitemap_and_probes(
    *,
    client: SafeHttpClient,
    root_url: str,
    queue: list[Candidate],
    queued_urls: set[str],
    budget: int,
) -> None:
    """Adds pages that following links alone would never reach.

    Runs once, straight after the homepage, and in two stages:

    1. The site's own sitemap, which lists public URLs regardless of how the
       navigation is built.
    2. Well-known paths for any page type still missing -- the fallback for
       sites with no sitemap *and* JavaScript navigation.
    """
    found_types = {candidate.page_type for candidate in queue}

    for url in discover_sitemap_urls(client, root_url):
        if url in queued_urls or len(queued_urls) >= budget * 2:
            continue
        page_type = classify_page_type(url)
        queued_urls.add(url)
        queue.append(
            Candidate(
                priority=TYPE_PRIORITY.get(page_type, TYPE_PRIORITY[PageType.OTHER]),
                depth=1,
                url=url,
                page_type=page_type,
            )
        )
        found_types.add(page_type)

    for candidate in probe_candidates(root_url, already_found=found_types):
        if candidate.url in queued_urls:
            continue
        queued_urls.add(candidate.url)
        queue.append(candidate)


def _record_page(
    scan: Scan,
    candidate: Candidate,
    *,
    status_code: int | None,
    title: str,
    emails_found: int,
    final_url: str | None = None,
) -> Page:
    """Saves the page that was fetched.

    Failed fetches are recorded too (with no status code) so the scan report
    shows what was attempted, not only what succeeded.
    """
    url = final_url or candidate.url
    page_type = candidate.page_type
    if final_url and final_url != candidate.url and candidate.depth > 0:
        # A redirect can land somewhere with a different purpose.
        page_type = classify_page_type(final_url) or candidate.page_type

    page, _ = Page.objects.update_or_create(
        scan=scan,
        url=url[:1000],
        defaults={
            "company": scan.company,
            "page_type": page_type,
            "title": title,
            "status_code": status_code,
            "emails_found": emails_found,
            "fetched_at": timezone.now() if status_code else None,
        },
    )
    return page


def _bump_scanned(scan: Scan) -> None:
    """Persists progress after every page so the status endpoint stays live."""
    scan.pages_scanned += 1
    scan.save(
        update_fields=["pages_scanned", "pages_discovered", "contacts_found", "updated_at"]
    )


def _save_contacts(*, scan: Scan, page: Page, emails: list[str]) -> int:
    """Stores newly discovered addresses, returning how many were new.

    Uniqueness is per (company, email), so the same address appearing on the
    careers page and the contact page is stored once -- as the specification
    requires.
    """
    from apps.contacts.classification import classify_email
    from apps.contacts.models import Contact

    created_count = 0
    for email in emails:
        try:
            with transaction.atomic():
                _, created = Contact.objects.get_or_create(
                    company=scan.company,
                    email=email,
                    defaults={
                        "user": scan.user,
                        "classification": classify_email(email),
                        "source_page": page,
                        "source_url": page.url,
                    },
                )
        except IntegrityError:
            # Lost a race against a concurrent scan; the row exists either way.
            continue
        if created:
            created_count += 1
    return created_count
