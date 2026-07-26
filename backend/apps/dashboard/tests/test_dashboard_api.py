"""Tests for GET /api/dashboard/."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.applications.models import Application, ApplicationStatus
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.crawler.models import Scan, ScanStatus
from apps.dashboard.services import build_dashboard

pytestmark = pytest.mark.django_db

URL = reverse("api:dashboard")


@pytest.fixture
def populated(user, company):
    """A user with a deliberately mixed set of records."""
    second = Company.objects.create(user=user, name="Globex", website="https://globex.example")
    third = Company.objects.create(user=user, name="Initech", website="https://initech.example")

    # Only `company` and `second` have completed scans; `third` has a failure.
    Scan.objects.create(
        user=user, company=company, target_url=company.website, status=ScanStatus.COMPLETED
    )
    Scan.objects.create(
        user=user, company=second, target_url=second.website, status=ScanStatus.COMPLETED
    )
    Scan.objects.create(
        user=user, company=third, target_url=third.website, status=ScanStatus.FAILED
    )

    Contact.objects.create(user=user, company=company, email="careers@acme.example")
    Contact.objects.create(user=user, company=company, email="hr@acme.example", is_favourite=True)
    Contact.objects.create(user=user, company=second, email="jobs@globex.example")

    for status in (
        ApplicationStatus.DRAFT,
        ApplicationStatus.SENT,
        ApplicationStatus.SENT,
        ApplicationStatus.WAITING,
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.CLOSED,
    ):
        Application.objects.create(
            user=user, company=company, position=f"Role {status}", status=status
        )

    return {"companies": [company, second, third]}


class TestDashboardCounters:
    def test_company_counters(self, auth_client, populated):
        body = auth_client.get(URL).json()

        assert body["total_companies"] == 3
        # A failed scan does not make a company "scanned".
        assert body["companies_scanned"] == 2

    def test_contact_counters(self, auth_client, populated):
        body = auth_client.get(URL).json()

        assert body["total_contacts"] == 3
        assert body["favourite_contacts"] == 1

    def test_application_counters(self, auth_client, populated):
        body = auth_client.get(URL).json()

        assert body["total_applications"] == 9
        assert body["drafts"] == 1
        # "Sent" means anything past draft, whatever its current status.
        assert body["applications_sent"] == 8
        assert body["pending_applications"] == 3  # 2 sent + 1 waiting
        assert body["interviews"] == 1
        assert body["offers"] == 1
        assert body["rejections"] == 2

    def test_full_status_breakdown(self, auth_client, populated):
        body = auth_client.get(URL).json()

        assert body["applications_by_status"] == {
            "draft": 1,
            "sent": 2,
            "waiting": 1,
            "interview": 1,
            "offer": 1,
            "rejected": 2,
            "closed": 1,
        }

    def test_breakdown_sums_to_the_total(self, auth_client, populated):
        body = auth_client.get(URL).json()

        assert sum(body["applications_by_status"].values()) == body["total_applications"]

    def test_a_company_with_several_completed_scans_counts_once(self, auth_client, user, company):
        for _ in range(3):
            Scan.objects.create(
                user=user,
                company=company,
                target_url=company.website,
                status=ScanStatus.COMPLETED,
            )

        assert auth_client.get(URL).json()["companies_scanned"] == 1


class TestDashboardIsolation:
    def test_empty_account_reports_zeroes(self, auth_client):
        body = auth_client.get(URL).json()

        assert body["total_companies"] == 0
        assert body["total_contacts"] == 0
        assert body["total_applications"] == 0
        assert body["applications_by_status"]["sent"] == 0

    def test_another_users_data_is_excluded(
        self, auth_client, populated, other_user, other_company
    ):
        Contact.objects.create(
            user=other_user, company=other_company, email="theirs@other.example"
        )
        Application.objects.create(
            user=other_user,
            company=other_company,
            position="Theirs",
            status=ApplicationStatus.OFFER,
        )
        Scan.objects.create(
            user=other_user,
            company=other_company,
            target_url=other_company.website,
            status=ScanStatus.COMPLETED,
        )

        body = auth_client.get(URL).json()

        assert body["total_companies"] == 3
        assert body["total_contacts"] == 3
        assert body["total_applications"] == 9
        assert body["offers"] == 1

    def test_requires_authentication(self, api_client):
        assert api_client.get(URL).status_code == 401


class TestDashboardPerformance:
    """The dashboard is the landing page; it must not scale with row count."""

    def test_the_aggregation_is_three_queries(self, populated, user, django_assert_num_queries):
        # One aggregate per app: companies, contacts, applications. Measured on
        # the service so the count is not muddied by JWT authentication and the
        # request's transaction savepoints.
        with django_assert_num_queries(3):
            build_dashboard(user=user)

    def test_query_count_does_not_grow_with_data(self, auth_client, populated, user):
        with CaptureQueriesContext(connection) as baseline:
            auth_client.get(URL)

        for index in range(20):
            extra = Company.objects.create(
                user=user, name=f"Extra {index}", website=f"https://extra{index}.example"
            )
            Contact.objects.create(user=user, company=extra, email=f"hr{index}@extra.example")
            Application.objects.create(
                user=user, company=extra, position="Engineer", status=ApplicationStatus.SENT
            )

        with CaptureQueriesContext(connection) as after:
            auth_client.get(URL)

        # 21x the data, identical query count. Catches any future change that
        # introduces a per-row query.
        assert len(after) == len(baseline)
