"""Cancelling a scan.

Two situations behave differently and both matter:

* a **queued** scan is revoked before it starts, so nothing was done and
  nothing is kept;
* a **running** scan is stopped cooperatively, so the pages and contacts found
  before the request must survive.
"""

import pytest
from django.urls import reverse

from apps.contacts.models import Contact
from apps.crawler.models import Page, Scan, ScanStatus
from apps.crawler.services import scanner
from apps.crawler.tests.fakes import FakeHttpClient, install
from apps.crawler.tests.test_scanner import SITE

pytestmark = pytest.mark.django_db


def cancel_url(scan_id) -> str:
    return reverse("api:scan-cancel", args=[scan_id])


@pytest.fixture
def scan(user, company):
    return Scan.objects.create(user=user, company=company, target_url=company.website)


class TestCancelQueuedScan:
    def test_marks_it_cancelled_immediately(self, scan):
        result = scanner.cancel_scan(scan=scan)

        assert result.status == ScanStatus.CANCELLED
        assert result.cancel_requested is True
        assert result.finished_at is not None
        assert result.is_active is False

    def test_a_cancelled_scan_is_skipped_by_the_worker(self, scan, monkeypatch):
        client = install(monkeypatch, FakeHttpClient(dict(SITE)))
        scanner.cancel_scan(scan=scan)

        # Simulates the task being delivered after the cancellation.
        result = scanner.run_scan(scan_id=scan.pk)

        assert result.status == ScanStatus.CANCELLED
        assert client.requested == [], "no page should have been fetched"
        assert Page.objects.filter(scan=scan).count() == 0

    def test_cancelling_frees_the_company_for_a_new_scan(self, scan, user, company):
        scanner.cancel_scan(scan=scan)

        # start_scan refuses a second *active* scan; a cancelled one is not.
        second = scanner.start_scan(user=user, company=company)

        assert second.pk != scan.pk
        assert second.status == ScanStatus.PENDING


class TestCancelRunningScan:
    def test_stops_mid_crawl_and_keeps_what_it_found(self, scan, monkeypatch):
        # Request cancellation once the crawl has fetched two pages, which is
        # what a user clicking the button partway through looks like.
        real_check = scanner.is_cancellation_requested
        calls = {"n": 0}

        def cancel_after_two_pages(s):
            calls["n"] += 1
            if calls["n"] > 2:
                Scan.objects.filter(pk=s.pk).update(cancel_requested=True)
            return real_check(s)

        monkeypatch.setattr(scanner, "is_cancellation_requested", cancel_after_two_pages)
        install(monkeypatch, FakeHttpClient(dict(SITE)))

        result = scanner.run_scan(scan_id=scan.pk)

        assert result.status == ScanStatus.CANCELLED
        assert result.finished_at is not None
        # The point of cooperative cancellation: partial work survives.
        assert 0 < result.pages_scanned < len(SITE)
        assert Page.objects.filter(scan=scan).count() == result.pages_scanned

    def test_contacts_found_before_cancelling_are_kept(self, scan, monkeypatch, company):
        real_check = scanner.is_cancellation_requested
        calls = {"n": 0}

        def cancel_after_three_pages(s):
            calls["n"] += 1
            if calls["n"] > 3:
                Scan.objects.filter(pk=s.pk).update(cancel_requested=True)
            return real_check(s)

        monkeypatch.setattr(scanner, "is_cancellation_requested", cancel_after_three_pages)
        install(monkeypatch, FakeHttpClient(dict(SITE)))

        scanner.run_scan(scan_id=scan.pk)

        assert Contact.objects.filter(company=company).exists()

    def test_a_running_scan_is_not_closed_out_until_the_worker_stops(self, scan):
        scan.status = ScanStatus.RUNNING
        scan.save(update_fields=["status"])

        result = scanner.cancel_scan(scan=scan)

        # Still "running": only the worker can decide it has actually stopped,
        # and it records the final counters when it does.
        assert result.cancel_requested is True
        assert result.status == ScanStatus.RUNNING


class TestCancelRules:
    @pytest.mark.parametrize(
        "status", [ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED]
    )
    def test_a_finished_scan_cannot_be_cancelled(self, scan, status):
        scan.status = status
        scan.save(update_fields=["status"])

        with pytest.raises(scanner.ScanNotCancellableError):
            scanner.cancel_scan(scan=scan)

    def test_can_be_cancelled_matches_is_active(self, scan):
        assert scan.can_be_cancelled is True

        scan.status = ScanStatus.COMPLETED
        assert scan.can_be_cancelled is False


class TestCancelEndpoint:
    def test_cancels_and_returns_the_scan(self, auth_client, scan):
        response = auth_client.post(cancel_url(scan.pk))

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == ScanStatus.CANCELLED
        assert body["is_active"] is False
        assert body["can_be_cancelled"] is False

    def test_trailing_slash_form_works(self, auth_client, scan):
        response = auth_client.post(f"{cancel_url(scan.pk)}/")

        assert response.status_code == 200

    def test_finished_scan_returns_409(self, auth_client, scan):
        scan.status = ScanStatus.COMPLETED
        scan.save(update_fields=["status"])

        response = auth_client.post(cancel_url(scan.pk))

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "scan_not_cancellable"

    def test_another_users_scan_is_not_found(self, auth_client, other_user, other_company):
        theirs = Scan.objects.create(
            user=other_user, company=other_company, target_url=other_company.website
        )

        response = auth_client.post(cancel_url(theirs.pk))

        assert response.status_code == 404
        theirs.refresh_from_db()
        assert theirs.cancel_requested is False

    def test_requires_authentication(self, api_client, scan):
        assert api_client.post(cancel_url(scan.pk)).status_code == 401

    def test_revoke_failure_does_not_break_cancellation(self, auth_client, scan, monkeypatch):
        # The broker being unreachable must not stop the flag being set --
        # the flag is what actually stops a running crawl.
        scan.task_id = "some-task-id"
        scan.save(update_fields=["task_id"])

        import config.celery

        def boom(*args, **kwargs):
            raise OSError("broker unreachable")

        monkeypatch.setattr(config.celery.app.control, "revoke", boom)

        response = auth_client.post(cancel_url(scan.pk))

        assert response.status_code == 200
        scan.refresh_from_db()
        assert scan.cancel_requested is True
