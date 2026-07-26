"""Tests for POST /api/scan/{company_id} and GET /api/scan/status/{scan_id}."""

import pytest
from django.urls import reverse

from apps.contacts.models import Contact
from apps.crawler.models import Scan, ScanStatus
from apps.crawler.tests.fakes import FakeHttpClient, install
from apps.crawler.tests.test_scanner import ROOT, SITE

pytestmark = pytest.mark.django_db


def scan_url(company_id) -> str:
    return reverse("api:scan-create", args=[company_id])


def status_url(scan_id) -> str:
    return reverse("api:scan-status", args=[scan_id])


@pytest.fixture
def site(monkeypatch):
    return install(monkeypatch, FakeHttpClient(dict(SITE)))


class TestStartScanEndpoint:
    def test_returns_202_with_a_pending_scan(self, auth_client, company):
        response = auth_client.post(scan_url(company.pk))

        assert response.status_code == 202
        body = response.json()
        assert body["status"] == ScanStatus.PENDING
        assert body["company"] == str(company.pk)
        assert body["target_url"] == company.website
        assert body["is_active"] is True

    def test_queues_and_runs_the_scan_on_commit(
        self, auth_client, company, site, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            response = auth_client.post(scan_url(company.pk))

        scan = Scan.objects.get(pk=response.json()["id"])
        assert scan.status == ScanStatus.COMPLETED
        assert scan.contacts_found > 0
        assert Contact.objects.filter(company=company).exists()

    def test_the_trailing_slash_form_also_works(self, auth_client, company):
        # One route accepts both spellings, so a POST to either reaches the
        # view directly rather than hitting an APPEND_SLASH redirect.
        response = auth_client.post(f"{scan_url(company.pk)}/")

        assert response.status_code == 202

    def test_rejects_a_concurrent_scan(self, auth_client, company):
        auth_client.post(scan_url(company.pk))

        response = auth_client.post(scan_url(company.pk))

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "scan_already_running"

    def test_another_users_company_is_not_found(self, auth_client, other_company):
        response = auth_client.post(scan_url(other_company.pk))

        assert response.status_code == 404
        assert Scan.objects.count() == 0

    def test_unknown_company_is_not_found(self, auth_client):
        response = auth_client.post(scan_url("00000000-0000-0000-0000-000000000000"))

        assert response.status_code == 404

    def test_rejects_a_non_public_website(self, auth_client, company, settings):
        settings.CRAWLER_ALLOW_PRIVATE_NETWORKS = False
        company.website = "http://169.254.169.254/latest/meta-data"
        company.save(update_fields=["website"])

        response = auth_client.post(scan_url(company.pk))

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_scan_target"
        assert Scan.objects.count() == 0

    def test_requires_authentication(self, api_client, company):
        assert api_client.post(scan_url(company.pk)).status_code == 401


class TestScanStatusEndpoint:
    def test_reports_progress_and_pages(
        self, auth_client, company, site, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            created = auth_client.post(scan_url(company.pk)).json()

        response = auth_client.get(status_url(created["id"]))

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == ScanStatus.COMPLETED
        assert body["progress_percent"] == 100
        assert body["is_active"] is False
        assert body["pages_scanned"] > 0
        assert len(body["pages"]) == body["pages_scanned"]

    def test_page_entries_carry_type_and_status(
        self, auth_client, company, site, django_capture_on_commit_callbacks
    ):
        with django_capture_on_commit_callbacks(execute=True):
            created = auth_client.post(scan_url(company.pk)).json()

        pages = auth_client.get(status_url(created["id"])).json()["pages"]
        homepage = next(page for page in pages if page["url"] == ROOT)

        assert homepage["page_type"] == "home"
        assert homepage["page_type_display"] == "Home"
        assert homepage["status_code"] == 200

    def test_pending_scan_reports_zero_progress(self, auth_client, company):
        created = auth_client.post(scan_url(company.pk)).json()

        body = auth_client.get(status_url(created["id"])).json()

        assert body["status"] == ScanStatus.PENDING
        assert body["progress_percent"] == 0
        assert body["is_active"] is True

    def test_failed_scan_exposes_the_error(
        self, auth_client, company, monkeypatch, django_capture_on_commit_callbacks
    ):
        install(monkeypatch, FakeHttpClient({}, failing={ROOT}))

        with django_capture_on_commit_callbacks(execute=True):
            created = auth_client.post(scan_url(company.pk)).json()

        body = auth_client.get(status_url(created["id"])).json()

        assert body["status"] == ScanStatus.FAILED
        assert body["error_message"]

    def test_another_users_scan_is_not_found(self, auth_client, other_user, other_company):
        theirs = Scan.objects.create(
            user=other_user, company=other_company, target_url=other_company.website
        )

        response = auth_client.get(status_url(theirs.pk))

        assert response.status_code == 404

    def test_requires_authentication(self, api_client, company, user):
        scan = Scan.objects.create(user=user, company=company, target_url=company.website)

        assert api_client.get(status_url(scan.pk)).status_code == 401
