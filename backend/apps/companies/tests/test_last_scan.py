"""The `last_scan` field on company detail.

Exists so the scan-progress screen can recover its scan id after a page
reload -- otherwise the id is only ever seen in the response to the POST that
started the scan.
"""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.crawler.models import Scan, ScanStatus

pytestmark = pytest.mark.django_db


def detail_url(company_id) -> str:
    return reverse("api:company-detail", args=[company_id])


class TestLastScan:
    def test_is_null_before_any_scan(self, auth_client, company):
        response = auth_client.get(detail_url(company.pk))

        assert response.status_code == 200
        assert response.json()["last_scan"] is None

    def test_returns_the_running_scan(self, auth_client, user, company):
        scan = Scan.objects.create(
            user=user,
            company=company,
            target_url=company.website,
            status=ScanStatus.RUNNING,
            pages_discovered=10,
            pages_scanned=4,
            contacts_found=2,
        )

        body = auth_client.get(detail_url(company.pk)).json()["last_scan"]

        assert body["id"] == str(scan.pk)
        assert body["status"] == ScanStatus.RUNNING
        assert body["is_active"] is True
        assert body["progress_percent"] == 40
        assert body["pages_scanned"] == 4
        assert body["contacts_found"] == 2

    def test_returns_the_most_recent_scan(self, auth_client, user, company):
        older = Scan.objects.create(
            user=user,
            company=company,
            target_url=company.website,
            status=ScanStatus.COMPLETED,
        )
        newest = Scan.objects.create(
            user=user,
            company=company,
            target_url=company.website,
            status=ScanStatus.PENDING,
        )
        # `auto_now_add` reads the system clock, whose resolution is coarse
        # enough that two rows written in a loop can share a timestamp. Space
        # them explicitly so "most recent" is actually well defined here.
        # In production `start_scan` refuses to queue a second scan while one
        # is active, so consecutive scans are always separated by a full crawl.
        Scan.objects.filter(pk=older.pk).update(created_at=timezone.now() - timedelta(hours=1))

        body = auth_client.get(detail_url(company.pk)).json()["last_scan"]

        assert body["id"] == str(newest.pk)

    def test_exposes_the_error_of_a_failed_scan(self, auth_client, user, company):
        Scan.objects.create(
            user=user,
            company=company,
            target_url=company.website,
            status=ScanStatus.FAILED,
            error_message="Could not fetch homepage.",
        )

        body = auth_client.get(detail_url(company.pk)).json()["last_scan"]

        assert body["status"] == ScanStatus.FAILED
        assert body["error_message"] == "Could not fetch homepage."
        assert body["is_active"] is False

    def test_the_list_endpoint_stays_lean(self, auth_client, user, company):
        Scan.objects.create(
            user=user, company=company, target_url=company.website, status=ScanStatus.COMPLETED
        )

        row = auth_client.get(reverse("api:company-list")).json()["results"][0]

        # Excluded from the list serializer: one extra query per row for a
        # value the companies list does not display.
        assert "last_scan" not in row

    def test_a_scan_started_through_the_api_is_recoverable(
        self, auth_client, company, monkeypatch
    ):
        from apps.crawler.tests.fakes import FakeHttpClient, install
        from apps.crawler.tests.test_scanner import ROOT, SITE

        install(monkeypatch, FakeHttpClient(dict(SITE)))
        started = auth_client.post(reverse("api:scan-create", args=[company.pk])).json()
        assert started["target_url"] == ROOT

        # Simulates the frontend reloading and having lost the POST response.
        recovered = auth_client.get(detail_url(company.pk)).json()["last_scan"]

        assert recovered["id"] == started["id"]
