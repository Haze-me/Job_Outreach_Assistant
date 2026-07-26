"""Tests for GET/PUT/PATCH /api/auth/profile/."""

import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db

URL = reverse("api:profile")


class TestRetrieveProfile:
    def test_returns_the_authenticated_user(self, auth_client, user):
        response = auth_client.get(URL)

        assert response.status_code == 200
        assert response.json()["id"] == str(user.pk)
        assert response.json()["email"] == user.email
        assert response.json()["full_name"] == "Ada Lovelace"

    def test_never_exposes_the_password_hash(self, auth_client):
        response = auth_client.get(URL)

        assert "password" not in response.json()

    def test_requires_authentication(self, api_client):
        response = api_client.get(URL)

        assert response.status_code == 401
        assert response.json()["error"]["code"] == "not_authenticated"

    def test_rejects_a_garbage_token(self, api_client):
        api_client.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")

        response = api_client.get(URL)

        assert response.status_code == 401


class TestUpdateProfile:
    def test_patch_updates_names(self, auth_client, user):
        response = auth_client.patch(URL, {"first_name": "Grace", "last_name": "Hopper"})

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == "Grace"
        assert user.last_name == "Hopper"

    def test_put_replaces_names(self, auth_client, user):
        response = auth_client.put(URL, {"first_name": "Grace", "last_name": "Hopper"})

        assert response.status_code == 200
        assert response.json()["full_name"] == "Grace Hopper"

    def test_names_are_trimmed(self, auth_client, user):
        auth_client.patch(URL, {"first_name": "   Grace   "})

        user.refresh_from_db()
        assert user.first_name == "Grace"

    def test_email_is_read_only(self, auth_client, user):
        original = user.email

        response = auth_client.patch(URL, {"email": "hijacked@example.com"})

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.email == original

    def test_privilege_fields_are_not_writable(self, auth_client, user):
        response = auth_client.patch(URL, {"is_staff": True, "is_superuser": True})

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.is_staff is False
        assert user.is_superuser is False

    def test_a_user_cannot_reach_another_users_profile(self, api_client, other_user, user):
        # The endpoint takes no id, so the only record reachable is your own.
        token = RefreshToken.for_user(other_user)
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

        response = api_client.get(URL)

        assert response.json()["id"] == str(other_user.pk)
        assert response.json()["id"] != str(user.pk)

    def test_requires_authentication(self, api_client):
        response = api_client.patch(URL, {"first_name": "Nobody"})

        assert response.status_code == 401
