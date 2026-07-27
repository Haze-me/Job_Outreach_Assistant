"""Scan and Page models.

A ``Scan`` is one crawl of one company website. Its ``Page`` rows record every
URL the crawl actually fetched, which is what makes a scan auditable: you can
see exactly which public pages were read and where each contact came from.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class ScanStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    RUNNING = "running", _("Running")
    COMPLETED = "completed", _("Completed")
    FAILED = "failed", _("Failed")
    CANCELLED = "cancelled", _("Cancelled")


class PageType(models.TextChoices):
    """The page kinds the specification asks the scanner to look for."""

    HOME = "home", _("Home")
    ABOUT = "about", _("About")
    CAREERS = "careers", _("Careers")
    JOBS = "jobs", _("Jobs")
    CONTACT = "contact", _("Contact")
    TEAM = "team", _("Team")
    LEADERSHIP = "leadership", _("Leadership")
    PRESS = "press", _("Press")
    OTHER = "other", _("Other")


class Scan(BaseModel):
    """One crawl of one company's website."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scans",
        verbose_name=_("owner"),
    )
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="scans",
        verbose_name=_("company"),
    )

    status = models.CharField(
        _("status"),
        max_length=20,
        choices=ScanStatus.choices,
        default=ScanStatus.PENDING,
        db_index=True,
    )
    # Snapshotted so a later edit to the company website does not rewrite the
    # history of what was actually crawled.
    target_url = models.URLField(_("target URL"), max_length=500)

    pages_discovered = models.PositiveIntegerField(_("pages discovered"), default=0)
    pages_scanned = models.PositiveIntegerField(_("pages scanned"), default=0)
    contacts_found = models.PositiveIntegerField(_("contacts found"), default=0)

    started_at = models.DateTimeField(_("started at"), null=True, blank=True)
    finished_at = models.DateTimeField(_("finished at"), null=True, blank=True)
    error_message = models.TextField(_("error message"), blank=True)

    task_id = models.CharField(
        _("Celery task id"),
        max_length=255,
        blank=True,
        help_text=_("Empty when the scan ran inline rather than on a worker."),
    )

    # Cancellation is cooperative rather than a process kill. The user sets
    # this flag; the crawl loop notices it between pages and stops cleanly,
    # keeping the pages and contacts already found. Terminating the worker
    # process instead would discard that work and leave the record stranded
    # mid-transition.
    cancel_requested = models.BooleanField(
        _("cancellation requested"),
        default=False,
        help_text=_("Set when a user asks to stop a scan that is already running."),
    )

    class Meta:
        verbose_name = _("scan")
        verbose_name_plural = _("scans")
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="scan_user_recent_idx"),
            models.Index(fields=["company", "-created_at"], name="scan_company_recent_idx"),
            models.Index(fields=["status"], name="scan_status_idx"),
        ]

    def __str__(self) -> str:
        return f"Scan of {self.target_url} ({self.status})"

    @property
    def is_active(self) -> bool:
        return self.status in {ScanStatus.PENDING, ScanStatus.RUNNING}

    @property
    def progress_percent(self) -> int:
        """Rough completion percentage for the scan-progress screen.

        A running scan keeps discovering pages, so the denominator moves; the
        value is capped at 99 until the scan actually finishes to avoid showing
        100% on a crawl that is still going.
        """
        if self.status == ScanStatus.COMPLETED:
            return 100
        if self.status == ScanStatus.FAILED:
            return 0
        if not self.pages_discovered:
            return 0
        # A cancelled scan keeps the fraction it genuinely reached rather than
        # jumping to 100 or resetting to 0 -- it did real work.
        return min(99, round(self.pages_scanned / self.pages_discovered * 100))

    @property
    def can_be_cancelled(self) -> bool:
        """Only a scan that has not finished can be stopped."""
        return self.is_active


class Page(BaseModel):
    """A single public page fetched during a scan."""

    scan = models.ForeignKey(
        Scan,
        on_delete=models.CASCADE,
        related_name="pages",
        verbose_name=_("scan"),
    )
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="pages",
        verbose_name=_("company"),
    )

    url = models.URLField(_("URL"), max_length=1000)
    page_type = models.CharField(
        _("page type"),
        max_length=20,
        choices=PageType.choices,
        default=PageType.OTHER,
    )
    title = models.CharField(_("title"), max_length=500, blank=True)
    status_code = models.PositiveSmallIntegerField(_("HTTP status"), null=True, blank=True)
    emails_found = models.PositiveIntegerField(_("emails found"), default=0)
    fetched_at = models.DateTimeField(_("fetched at"), null=True, blank=True)

    class Meta:
        verbose_name = _("page")
        verbose_name_plural = _("pages")
        ordering = ["created_at", "id"]
        constraints = [
            # A crawl must never fetch or record the same URL twice.
            models.UniqueConstraint(fields=["scan", "url"], name="unique_page_url_per_scan"),
        ]
        indexes = [
            models.Index(fields=["company", "-created_at"], name="page_company_recent_idx"),
            models.Index(fields=["scan", "page_type"], name="page_scan_type_idx"),
        ]

    def __str__(self) -> str:
        return self.url
