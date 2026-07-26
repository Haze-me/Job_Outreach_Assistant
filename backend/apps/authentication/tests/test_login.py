"""Tests for POST /api/auth/login/."""

import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken

pytestmark = pytest.mark.django_db

URL = reverse("api:login")


class TestLoginSuccess:
    def test_returns_token_pair_and_user(self, api_client, user, password):
        response = api_client.post(URL, {"email": user.email, "password": password})

        assert response.status_code == 200
        body = response.json()
        assert set(body) == {"access", "refresh", "user"}
        assert body["user"]["id"] == str(user.pk)
        assert body["user"]["email"] == user.email

    def test_email_is_case_and_whitespace_insensitive(self, api_client, user, password):
        response = api_client.post(
            URL, {"email": f"  {user.email.upper()}  ", "password": password}
        )

        assert response.status_code == 200

    def test_access_token_carries_email_claim(self, api_client, user, password):
        access = api_client.post(URL, {"email": user.email, "password": password}).json()["access"]

        assert AccessToken(access)["email"] == user.email

    def test_updates_last_login(self, api_client, user, password):
        assert user.last_login is None

        api_client.post(URL, {"email": user.email, "password": password})

        user.refresh_from_db()
        assert user.last_login is not None


class TestLoginFailure:
    def test_rejects_wrong_password(self, api_client, user):
        response = api_client.post(URL, {"email": user.email, "password": "Wrong-Passw0rd!"})

        assert response.status_code == 401

    def test_rejects_unknown_email(self, api_client):
        response = api_client.post(URL, {"email": "ghost@example.com", "password": "whatever1!"})

        assert response.status_code == 401

    def test_wrong_password_and_unknown_email_are_indistinguishable(self, api_client, user):
        wrong_password = api_client.post(URL, {"email": user.email, "password": "Wrong-Passw0rd!"})
        unknown_email = api_client.post(
            URL, {"email": "ghost@example.com", "password": "Wrong-Passw0rd!"}
        )

        # Differing responses would let an attacker enumerate registered emails.
        assert wrong_password.status_code == unknown_email.status_code
        assert wrong_password.json() == unknown_email.json()

    def test_rejects_inactive_user(self, api_client, user, password):
        user.is_active = False
        user.save(update_fields=["is_active"])

        response = api_client.post(URL, {"email": user.email, "password": password})

        assert response.status_code == 401

    def test_rejects_missing_credentials(self, api_client):
        response = api_client.post(URL, {})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "validation_error"
