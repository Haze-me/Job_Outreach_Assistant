"""Tests for /api/contacts/."""

import pytest
from django.urls import reverse

from apps.companies.models import Company
from apps.contacts.models import Contact, ContactClassification

pytestmark = pytest.mark.django_db

LIST_URL = reverse("api:contact-list")


def detail_url(contact_id) -> str:
    return reverse("api:contact-detail", args=[contact_id])


@pytest.fixture
def contacts(user, company):
    rows = [
        ("careers@acme.example", ContactClassification.CAREERS),
        ("recruitment@acme.example", ContactClassification.RECRUITMENT),
        ("support@acme.example", ContactClassification.SUPPORT),
        ("info@acme.example", ContactClassification.GENERAL),
    ]
    return [
        Contact.objects.create(
            user=user,
            company=company,
            email=email,
            classification=classification,
            source_url=f"{company.website}/contact",
        )
        for email, classification in rows
    ]


def emails(response) -> set[str]:
    return {row["email"] for row in response.json()["results"]}


class TestListContacts:
    def test_lists_only_your_contacts(self, auth_client, contacts, other_user, other_company):
        Contact.objects.create(
            user=other_user, company=other_company, email="theirs@other.example"
        )

        response = auth_client.get(LIST_URL)

        assert response.json()["count"] == 4
        assert "theirs@other.example" not in emails(response)

    def test_exposes_everything_the_contact_screen_needs(self, auth_client, contacts, company):
        row = auth_client.get(LIST_URL).json()["results"][0]

        expected = {"email", "classification", "source_url", "company_name", "date_discovered"}
        assert expected <= set(row)
        assert row["company_name"] == company.name

    def test_classification_display_is_human_readable(self, auth_client, contacts):
        rows = auth_client.get(LIST_URL).json()["results"]
        by_value = {row["classification"]: row["classification_display"] for row in rows}

        assert by_value["careers"] == "Careers"
        assert by_value["recruitment"] == "Recruitment"

    def test_requires_authentication(self, api_client):
        assert api_client.get(LIST_URL).status_code == 401


class TestSearchAndFilter:
    def test_search_by_email(self, auth_client, contacts):
        response = auth_client.get(LIST_URL, {"search": "careers"})

        assert emails(response) == {"careers@acme.example"}

    def test_search_by_company_name(self, auth_client, contacts):
        response = auth_client.get(LIST_URL, {"search": "Acme Robotics"})

        assert response.json()["count"] == 4

    def test_filter_by_classification(self, auth_client, contacts):
        response = auth_client.get(LIST_URL, {"classification": "support"})

        assert emails(response) == {"support@acme.example"}

    def test_filter_by_company(self, auth_client, contacts, company, user):
        second = Company.objects.create(user=user, name="Other Ltd", website="https://o.example")
        Contact.objects.create(user=user, company=second, email="x@o.example")

        response = auth_client.get(LIST_URL, {"company": str(company.pk)})

        assert response.json()["count"] == 4

    def test_recruitment_only_spans_related_categories(self, auth_client, contacts):
        response = auth_client.get(LIST_URL, {"recruitment_only": "true"})

        assert emails(response) == {"careers@acme.example", "recruitment@acme.example"}

    def test_filter_by_favourite(self, auth_client, contacts):
        favourite = contacts[0]
        favourite.is_favourite = True
        favourite.save(update_fields=["is_favourite"])

        response = auth_client.get(LIST_URL, {"is_favourite": "true"})

        assert emails(response) == {favourite.email}

    def test_invalid_classification_is_rejected(self, auth_client, contacts):
        response = auth_client.get(LIST_URL, {"classification": "not-a-category"})

        assert response.status_code == 400

    def test_order_by_email(self, auth_client, contacts):
        response = auth_client.get(LIST_URL, {"ordering": "email"})
        ordered = [row["email"] for row in response.json()["results"]]

        assert ordered == sorted(ordered)


class TestRetrieveContact:
    def test_returns_the_contact(self, auth_client, contacts):
        contact = contacts[0]

        response = auth_client.get(detail_url(contact.pk))

        assert response.status_code == 200
        assert response.json()["email"] == contact.email

    def test_another_users_contact_is_not_found(self, auth_client, other_user, other_company):
        theirs = Contact.objects.create(
            user=other_user, company=other_company, email="theirs@other.example"
        )

        assert auth_client.get(detail_url(theirs.pk)).status_code == 404


class TestAnnotateContact:
    def test_add_notes(self, auth_client, contacts):
        contact = contacts[0]

        response = auth_client.patch(detail_url(contact.pk), {"notes": "  Emailed on Monday.  "})

        assert response.status_code == 200
        contact.refresh_from_db()
        assert contact.notes == "Emailed on Monday."

    def test_mark_favourite(self, auth_client, contacts):
        contact = contacts[0]

        response = auth_client.patch(detail_url(contact.pk), {"is_favourite": True})

        assert response.status_code == 200
        contact.refresh_from_db()
        assert contact.is_favourite is True

    def test_email_and_classification_are_read_only(self, auth_client, contacts):
        contact = contacts[0]

        auth_client.patch(
            detail_url(contact.pk),
            {"email": "hijacked@evil.example", "classification": "hr"},
        )

        contact.refresh_from_db()
        assert contact.email == "careers@acme.example"
        assert contact.classification == ContactClassification.CAREERS

    def test_contacts_cannot_be_created_by_clients(self, auth_client, company):
        response = auth_client.post(
            LIST_URL, {"company": str(company.pk), "email": "made-up@acme.example"}
        )

        assert response.status_code == 405

    def test_contacts_cannot_be_deleted(self, auth_client, contacts):
        response = auth_client.delete(detail_url(contacts[0].pk))

        assert response.status_code == 405

    def test_cannot_annotate_another_users_contact(self, auth_client, other_user, other_company):
        theirs = Contact.objects.create(
            user=other_user, company=other_company, email="theirs@other.example"
        )

        response = auth_client.patch(detail_url(theirs.pk), {"is_favourite": True})

        assert response.status_code == 404


class TestDeduplication:
    def test_the_same_email_cannot_be_stored_twice_for_one_company(self, user, company):
        Contact.objects.create(user=user, company=company, email="hr@acme.example")

        from django.db import IntegrityError

        with pytest.raises(IntegrityError):
            Contact.objects.create(user=user, company=company, email="hr@acme.example")

    def test_the_same_email_may_exist_under_different_companies(self, user, company):
        second = Company.objects.create(user=user, name="Second Ltd", website="https://s.example")

        Contact.objects.create(user=user, company=company, email="hr@shared.example")
        Contact.objects.create(user=user, company=second, email="hr@shared.example")

        assert Contact.objects.filter(email="hr@shared.example").count() == 2
