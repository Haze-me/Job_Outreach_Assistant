"""Tests for /api/applications/."""

from datetime import date, timedelta

import pytest
from django.urls import reverse

from apps.applications.models import Application, ApplicationStatus
from apps.companies.models import Company
from apps.contacts.models import Contact

pytestmark = pytest.mark.django_db

LIST_URL = reverse("api:application-list")


def detail_url(application_id) -> str:
    return reverse("api:application-detail", args=[application_id])


@pytest.fixture
def contact(user, company):
    return Contact.objects.create(
        user=user, company=company, email="careers@acme.example", classification="careers"
    )


@pytest.fixture
def payload(company):
    return {
        "company": str(company.pk),
        "position": "Backend Engineer",
        "status": ApplicationStatus.DRAFT,
    }


class TestCreateApplication:
    def test_creates_and_assigns_owner(self, auth_client, payload, user, company):
        response = auth_client.post(LIST_URL, payload)

        assert response.status_code == 201
        application = Application.objects.get(pk=response.json()["id"])
        assert application.user == user
        assert application.company == company
        assert application.position == "Backend Engineer"

    def test_defaults_the_application_date_to_today(self, auth_client, payload):
        response = auth_client.post(LIST_URL, payload)

        assert response.json()["application_date"] == date.today().isoformat()

    def test_accepts_an_explicit_date(self, auth_client, payload):
        response = auth_client.post(LIST_URL, {**payload, "application_date": "2026-01-15"})

        assert response.json()["application_date"] == "2026-01-15"

    def test_trims_the_position(self, auth_client, payload):
        response = auth_client.post(LIST_URL, {**payload, "position": "  Data Analyst  "})

        assert response.json()["position"] == "Data Analyst"

    def test_links_a_contact_and_copies_its_email(self, auth_client, payload, contact):
        response = auth_client.post(LIST_URL, {**payload, "contact": str(contact.pk)})

        assert response.status_code == 201
        assert response.json()["contact_email"] == "careers@acme.example"

    def test_an_explicit_contact_email_is_not_overwritten(self, auth_client, payload, contact):
        response = auth_client.post(
            LIST_URL,
            {**payload, "contact": str(contact.pk), "contact_email": "someone@acme.example"},
        )

        assert response.json()["contact_email"] == "someone@acme.example"

    def test_contact_email_alone_is_allowed(self, auth_client, payload):
        response = auth_client.post(LIST_URL, {**payload, "contact_email": "hr@acme.example"})

        assert response.status_code == 201
        assert response.json()["contact"] is None

    def test_exposes_status_helpers(self, auth_client, payload):
        response = auth_client.post(LIST_URL, {**payload, "status": ApplicationStatus.INTERVIEW})

        body = response.json()
        assert body["status_display"] == "Interview"
        assert body["is_sent"] is True
        assert body["is_pending"] is False

    def test_requires_authentication(self, api_client, payload):
        assert api_client.post(LIST_URL, payload).status_code == 401


class TestCreateValidation:
    def test_position_is_required(self, auth_client, company):
        response = auth_client.post(
            LIST_URL, {"company": str(company.pk), "status": ApplicationStatus.DRAFT}
        )

        assert response.status_code == 400
        assert "position" in response.json()["error"]["details"]

    def test_blank_position_is_rejected(self, auth_client, payload):
        response = auth_client.post(LIST_URL, {**payload, "position": "   "})

        assert response.status_code == 400
        assert "position" in response.json()["error"]["details"]

    def test_company_is_required(self, auth_client):
        response = auth_client.post(
            LIST_URL, {"position": "Engineer", "status": ApplicationStatus.DRAFT}
        )

        assert response.status_code == 400
        assert "company" in response.json()["error"]["details"]

    def test_status_is_required(self, auth_client, company):
        response = auth_client.post(
            LIST_URL, {"company": str(company.pk), "position": "Engineer"}
        )

        assert response.status_code == 400
        assert "status" in response.json()["error"]["details"]

    def test_invalid_status_is_rejected(self, auth_client, payload):
        response = auth_client.post(LIST_URL, {**payload, "status": "employed"})

        assert response.status_code == 400
        assert "status" in response.json()["error"]["details"]

    def test_cannot_apply_to_another_users_company(self, auth_client, other_company):
        response = auth_client.post(
            LIST_URL,
            {
                "company": str(other_company.pk),
                "position": "Engineer",
                "status": ApplicationStatus.DRAFT,
            },
        )

        assert response.status_code == 400
        assert "company" in response.json()["error"]["details"]
        assert Application.objects.count() == 0

    def test_cannot_link_another_users_contact(
        self, auth_client, payload, other_user, other_company
    ):
        theirs = Contact.objects.create(
            user=other_user, company=other_company, email="theirs@other.example"
        )

        response = auth_client.post(LIST_URL, {**payload, "contact": str(theirs.pk)})

        assert response.status_code == 400
        assert "contact" in response.json()["error"]["details"]

    def test_contact_must_belong_to_the_same_company(self, auth_client, payload, user, contact):
        other = Company.objects.create(user=user, name="Other Ltd", website="https://o.example")

        response = auth_client.post(
            LIST_URL, {**payload, "company": str(other.pk), "contact": str(contact.pk)}
        )

        assert response.status_code == 400
        assert "contact" in response.json()["error"]["details"]


class TestListAndFilter:
    @pytest.fixture
    def applications(self, user, company):
        rows = [
            ("Backend Engineer", ApplicationStatus.DRAFT),
            ("Frontend Engineer", ApplicationStatus.SENT),
            ("Data Analyst", ApplicationStatus.WAITING),
            ("Platform Engineer", ApplicationStatus.INTERVIEW),
            ("SRE", ApplicationStatus.OFFER),
            ("QA Engineer", ApplicationStatus.REJECTED),
        ]
        return [
            Application.objects.create(
                user=user,
                company=company,
                position=position,
                status=status,
                application_date=date(2026, 1, 10) + timedelta(days=index),
            )
            for index, (position, status) in enumerate(rows)
        ]

    def positions(self, response) -> set[str]:
        return {row["position"] for row in response.json()["results"]}

    def test_lists_only_your_applications(
        self, auth_client, applications, other_user, other_company
    ):
        Application.objects.create(
            user=other_user,
            company=other_company,
            position="Theirs",
            status=ApplicationStatus.SENT,
        )

        response = auth_client.get(LIST_URL)

        assert response.json()["count"] == 6
        assert "Theirs" not in self.positions(response)

    def test_newest_application_date_first(self, auth_client, applications):
        first = auth_client.get(LIST_URL).json()["results"][0]

        assert first["position"] == "QA Engineer"

    def test_filter_by_status(self, auth_client, applications):
        response = auth_client.get(LIST_URL, {"status": ApplicationStatus.INTERVIEW})

        assert self.positions(response) == {"Platform Engineer"}

    def test_filter_is_sent_excludes_drafts(self, auth_client, applications):
        response = auth_client.get(LIST_URL, {"is_sent": "true"})

        assert response.json()["count"] == 5
        assert "Backend Engineer" not in self.positions(response)

    def test_filter_is_pending(self, auth_client, applications):
        response = auth_client.get(LIST_URL, {"is_pending": "true"})

        assert self.positions(response) == {"Frontend Engineer", "Data Analyst"}

    def test_filter_by_date_range(self, auth_client, applications):
        response = auth_client.get(
            LIST_URL, {"applied_after": "2026-01-12", "applied_before": "2026-01-13"}
        )

        assert self.positions(response) == {"Data Analyst", "Platform Engineer"}

    def test_search_by_position(self, auth_client, applications):
        response = auth_client.get(LIST_URL, {"search": "engineer"})

        assert response.json()["count"] == 4

    def test_search_by_company_name(self, auth_client, applications):
        response = auth_client.get(LIST_URL, {"search": "Acme Robotics"})

        assert response.json()["count"] == 6

    def test_order_by_position(self, auth_client, applications):
        response = auth_client.get(LIST_URL, {"ordering": "position"})
        ordered = [row["position"] for row in response.json()["results"]]

        assert ordered == sorted(ordered)


class TestUpdateAndDelete:
    @pytest.fixture
    def application(self, user, company):
        return Application.objects.create(
            user=user,
            company=company,
            position="Backend Engineer",
            status=ApplicationStatus.DRAFT,
            notes="Draft notes.",
        )

    def test_patch_advances_the_status(self, auth_client, application):
        response = auth_client.patch(
            detail_url(application.pk), {"status": ApplicationStatus.INTERVIEW}
        )

        assert response.status_code == 200
        application.refresh_from_db()
        assert application.status == ApplicationStatus.INTERVIEW
        assert application.position == "Backend Engineer"

    def test_put_replaces_optional_fields(self, auth_client, application, company):
        response = auth_client.put(
            detail_url(application.pk),
            {
                "company": str(company.pk),
                "position": "Backend Engineer",
                "status": ApplicationStatus.SENT,
            },
        )

        assert response.status_code == 200
        application.refresh_from_db()
        assert application.notes == ""

    def test_delete_removes_the_application(self, auth_client, application):
        response = auth_client.delete(detail_url(application.pk))

        assert response.status_code == 204
        assert not Application.objects.filter(pk=application.pk).exists()

    def test_cannot_touch_another_users_application(self, auth_client, other_user, other_company):
        theirs = Application.objects.create(
            user=other_user, company=other_company, position="Theirs", status=ApplicationStatus.SENT
        )

        assert auth_client.get(detail_url(theirs.pk)).status_code == 404
        assert auth_client.patch(detail_url(theirs.pk), {"status": "offer"}).status_code == 404
        assert auth_client.delete(detail_url(theirs.pk)).status_code == 404
        assert Application.objects.filter(pk=theirs.pk).exists()


class TestContactLifecycle:
    def test_deleting_a_contact_keeps_the_application_and_its_email(
        self, auth_client, user, company, contact
    ):
        application = Application.objects.create(
            user=user,
            company=company,
            position="Backend Engineer",
            status=ApplicationStatus.SENT,
            contact=contact,
            contact_email=contact.email,
        )

        contact.delete()

        application.refresh_from_db()
        assert application.contact is None
        assert application.contact_email == "careers@acme.example"

    def test_deleting_a_company_cascades_to_applications(self, user, company):
        application = Application.objects.create(
            user=user, company=company, position="Engineer", status=ApplicationStatus.SENT
        )

        company.delete()

        assert not Application.objects.filter(pk=application.pk).exists()
