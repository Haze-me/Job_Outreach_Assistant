"""Tests for /api/notes/."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.companies.models import Company, Note

pytestmark = pytest.mark.django_db

LIST_URL = reverse("api:note-list")


def detail_url(note_id) -> str:
    return reverse("api:note-detail", args=[note_id])


class TestCreateNote:
    def test_creates_a_note_for_a_company(self, auth_client, company, user):
        response = auth_client.post(
            LIST_URL, {"company": str(company.pk), "content": "Waiting for response."}
        )

        assert response.status_code == 201
        created = Note.objects.get(pk=response.json()["id"])
        assert created.company == company
        assert created.user == user

    def test_returns_the_company_name(self, auth_client, company):
        response = auth_client.post(
            LIST_URL, {"company": str(company.pk), "content": "Recruiter replied."}
        )

        assert response.json()["company_name"] == company.name

    def test_content_is_trimmed(self, auth_client, company):
        response = auth_client.post(
            LIST_URL, {"company": str(company.pk), "content": "  Follow up next week.  "}
        )

        assert response.json()["content"] == "Follow up next week."

    def test_cannot_attach_a_note_to_another_users_company(self, auth_client, other_company):
        response = auth_client.post(
            LIST_URL, {"company": str(other_company.pk), "content": "Sneaky."}
        )

        assert response.status_code == 400
        assert "company" in response.json()["error"]["details"]
        assert Note.objects.count() == 0

    def test_rejects_blank_content(self, auth_client, company):
        response = auth_client.post(LIST_URL, {"company": str(company.pk), "content": "   "})

        assert response.status_code == 400
        assert "content" in response.json()["error"]["details"]

    def test_requires_a_company(self, auth_client):
        response = auth_client.post(LIST_URL, {"content": "Orphan note."})

        assert response.status_code == 400
        assert "company" in response.json()["error"]["details"]

    def test_requires_authentication(self, api_client, company):
        response = api_client.post(LIST_URL, {"company": str(company.pk), "content": "Nope."})

        assert response.status_code == 401


class TestListNotes:
    @pytest.fixture
    def two_companies_with_notes(self, user):
        first = Company.objects.create(user=user, name="First Ltd", website="https://first.test")
        second = Company.objects.create(user=user, name="Second Ltd", website="https://second.test")
        notes = [
            Note.objects.create(user=user, company=first, content="Applied via careers email."),
            Note.objects.create(user=user, company=first, content="Follow up next week."),
            Note.objects.create(user=user, company=second, content="Recruiter replied."),
        ]

        # See the `catalogue` fixture in test_company_search.py: auto_now_add
        # cannot be relied on to produce distinct timestamps within a loop.
        base = timezone.now() - timedelta(hours=len(notes))
        for offset, created in enumerate(notes):
            Note.objects.filter(pk=created.pk).update(created_at=base + timedelta(hours=offset))

        return first, second

    def test_lists_only_your_notes(self, auth_client, note, other_user, other_company):
        Note.objects.create(user=other_user, company=other_company, content="Theirs.")

        response = auth_client.get(LIST_URL)

        assert response.json()["count"] == 1

    def test_filter_by_company(self, auth_client, two_companies_with_notes):
        first, _ = two_companies_with_notes

        response = auth_client.get(LIST_URL, {"company": str(first.pk)})

        assert response.json()["count"] == 2

    def test_filtering_by_another_users_company_returns_nothing(
        self, auth_client, note, other_company
    ):
        response = auth_client.get(LIST_URL, {"company": str(other_company.pk)})

        assert response.json()["count"] == 0

    def test_newest_first(self, auth_client, two_companies_with_notes):
        contents = [row["content"] for row in auth_client.get(LIST_URL).json()["results"]]

        assert contents[0] == "Recruiter replied."

    def test_search_by_content(self, auth_client, two_companies_with_notes):
        response = auth_client.get(LIST_URL, {"search": "recruiter"})

        assert response.json()["count"] == 1


class TestUpdateAndDeleteNote:
    def test_patch_updates_content(self, auth_client, note):
        response = auth_client.patch(detail_url(note.pk), {"content": "Updated."})

        assert response.status_code == 200
        note.refresh_from_db()
        assert note.content == "Updated."

    def test_delete_removes_the_note(self, auth_client, note):
        response = auth_client.delete(detail_url(note.pk))

        assert response.status_code == 204
        assert not Note.objects.filter(pk=note.pk).exists()

    def test_cannot_touch_another_users_note(self, auth_client, other_user, other_company):
        theirs = Note.objects.create(user=other_user, company=other_company, content="Theirs.")

        assert auth_client.get(detail_url(theirs.pk)).status_code == 404
        assert auth_client.patch(detail_url(theirs.pk), {"content": "x"}).status_code == 404
        assert auth_client.delete(detail_url(theirs.pk)).status_code == 404
        assert Note.objects.filter(pk=theirs.pk).exists()

    def test_cannot_move_a_note_to_another_users_company(self, auth_client, note, other_company):
        response = auth_client.patch(detail_url(note.pk), {"company": str(other_company.pk)})

        assert response.status_code == 400
        note.refresh_from_db()
        assert note.company_id != other_company.pk


class TestCompanyNotesField:
    """The company's own free-text `notes` field is separate from Note rows."""

    def test_company_notes_field_is_independent_of_note_rows(self, auth_client, company, note):
        response = auth_client.patch(
            reverse("api:company-detail", args=[company.pk]),
            {"notes": "Quick scratchpad text."},
        )

        assert response.status_code == 200
        assert response.json()["notes"] == "Quick scratchpad text."
        # The timestamped note is untouched.
        assert response.json()["notes_count"] == 1
        note.refresh_from_db()
        assert note.content == "Applied through careers email."
