"""CRUD tests for /api/companies/."""

import pytest
from django.urls import reverse

from apps.companies.models import Company

pytestmark = pytest.mark.django_db

LIST_URL = reverse("api:company-list")


def detail_url(company_id) -> str:
    return reverse("api:company-detail", args=[company_id])


VALID_PAYLOAD = {
    "name": "Globex Corporation",
    "website": "globex.example.com",
    "industry": "Software",
    "country": "Ireland",
    "description": "Enterprise tooling.",
    "notes": "Careers page looks active.",
}


class TestCreateCompany:
    def test_creates_and_assigns_owner(self, auth_client, user):
        response = auth_client.post(LIST_URL, VALID_PAYLOAD)

        assert response.status_code == 201
        company = Company.objects.get(name="Globex Corporation")
        assert company.user == user

    def test_normalises_the_website(self, auth_client):
        response = auth_client.post(
            LIST_URL, {**VALID_PAYLOAD, "website": "  GLOBEX.example.com/ "}
        )

        assert response.status_code == 201
        assert response.json()["website"] == "https://globex.example.com"

    def test_trims_the_name(self, auth_client):
        response = auth_client.post(LIST_URL, {**VALID_PAYLOAD, "name": "   Globex   "})

        assert response.json()["name"] == "Globex"

    def test_optional_fields_may_be_omitted(self, auth_client):
        response = auth_client.post(
            LIST_URL, {"name": "Minimal Ltd", "website": "minimal.example.com"}
        )

        assert response.status_code == 201
        assert response.json()["industry"] == ""
        assert response.json()["description"] == ""

    def test_exposes_date_added(self, auth_client):
        response = auth_client.post(LIST_URL, VALID_PAYLOAD)

        body = response.json()
        assert body["date_added"] == body["created_at"]

    def test_owner_cannot_be_spoofed(self, auth_client, other_user, user):
        response = auth_client.post(LIST_URL, {**VALID_PAYLOAD, "user": str(other_user.pk)})

        assert response.status_code == 201
        assert Company.objects.get(name="Globex Corporation").user == user

    def test_requires_authentication(self, api_client):
        response = api_client.post(LIST_URL, VALID_PAYLOAD)

        assert response.status_code == 401


class TestCreateCompanyValidation:
    def test_rejects_duplicate_name_for_same_user(self, auth_client, company):
        response = auth_client.post(
            LIST_URL, {"name": company.name, "website": "other.example.com"}
        )

        assert response.status_code == 400
        assert "name" in response.json()["error"]["details"]

    def test_duplicate_check_is_case_insensitive(self, auth_client, company):
        response = auth_client.post(
            LIST_URL, {"name": company.name.upper(), "website": "other.example.com"}
        )

        assert response.status_code == 400

    def test_the_same_name_is_allowed_for_a_different_user(self, auth_client, other_company):
        # Two job seekers may both track the same employer.
        response = auth_client.post(
            LIST_URL, {"name": other_company.name, "website": "mine.example.com"}
        )

        assert response.status_code == 201

    @pytest.mark.parametrize(
        "website",
        ["not a url", "ftp://example.com", "javascript:alert(1)", "http://localhost:8000", ""],
    )
    def test_rejects_invalid_websites(self, auth_client, website):
        response = auth_client.post(LIST_URL, {"name": "Test Ltd", "website": website})

        assert response.status_code == 400
        assert "website" in response.json()["error"]["details"]

    def test_rejects_missing_required_fields(self, auth_client):
        response = auth_client.post(LIST_URL, {})

        details = response.json()["error"]["details"]
        assert {"name", "website"} <= set(details)

    def test_rejects_blank_name(self, auth_client):
        response = auth_client.post(LIST_URL, {"name": "   ", "website": "example.com"})

        assert response.status_code == 400
        assert "name" in response.json()["error"]["details"]


class TestRetrieveCompany:
    def test_returns_full_detail(self, auth_client, company):
        response = auth_client.get(detail_url(company.pk))

        assert response.status_code == 200
        body = response.json()
        assert body["name"] == company.name
        assert body["description"] == "Industrial automation."
        assert body["notes_count"] == 0

    def test_counts_notes(self, auth_client, company, note):
        response = auth_client.get(detail_url(company.pk))

        assert response.json()["notes_count"] == 1

    def test_another_users_company_is_not_found(self, auth_client, other_company):
        response = auth_client.get(detail_url(other_company.pk))

        # 404, not 403: a 403 would confirm the id exists.
        assert response.status_code == 404

    def test_unknown_id_is_not_found(self, auth_client):
        response = auth_client.get(detail_url("00000000-0000-0000-0000-000000000000"))

        assert response.status_code == 404


class TestUpdateCompany:
    def test_patch_updates_fields(self, auth_client, company):
        response = auth_client.patch(detail_url(company.pk), {"industry": "Robotics"})

        assert response.status_code == 200
        company.refresh_from_db()
        assert company.industry == "Robotics"
        assert company.name == "Acme Robotics"

    def test_put_replaces_the_record(self, auth_client, company):
        response = auth_client.put(
            detail_url(company.pk), {"name": "Acme Robotics", "website": "acme.example.org"}
        )

        assert response.status_code == 200
        company.refresh_from_db()
        assert company.website == "https://acme.example.org"
        assert company.industry == ""

    def test_keeping_its_own_name_is_allowed(self, auth_client, company):
        response = auth_client.patch(detail_url(company.pk), {"name": company.name})

        assert response.status_code == 200

    def test_cannot_take_another_of_your_companies_names(self, auth_client, company, user):
        other = Company.objects.create(user=user, name="Initech", website="https://initech.test")

        response = auth_client.patch(detail_url(other.pk), {"name": company.name})

        assert response.status_code == 400
        assert "name" in response.json()["error"]["details"]

    def test_website_is_normalised_on_update(self, auth_client, company):
        response = auth_client.patch(detail_url(company.pk), {"website": "ACME.example.net/"})

        assert response.json()["website"] == "https://acme.example.net"

    def test_cannot_update_another_users_company(self, auth_client, other_company):
        response = auth_client.patch(detail_url(other_company.pk), {"name": "Hijacked"})

        assert response.status_code == 404
        other_company.refresh_from_db()
        assert other_company.name == "Not Yours Ltd"


class TestDeleteCompany:
    def test_deletes(self, auth_client, company):
        response = auth_client.delete(detail_url(company.pk))

        assert response.status_code == 204
        assert not Company.objects.filter(pk=company.pk).exists()

    def test_cascades_to_notes(self, auth_client, company, note):
        from apps.companies.models import Note

        auth_client.delete(detail_url(company.pk))

        assert not Note.objects.filter(pk=note.pk).exists()

    def test_cannot_delete_another_users_company(self, auth_client, other_company):
        response = auth_client.delete(detail_url(other_company.pk))

        assert response.status_code == 404
        assert Company.objects.filter(pk=other_company.pk).exists()
