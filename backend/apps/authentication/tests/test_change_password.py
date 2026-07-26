"""Tests for POST /api/auth/change-password/."""

import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db

URL = reverse("api:change-password")
REFRESH_URL = reverse("api:token-refresh")

NEW_PASSWORD = "An0ther-Str0ng-Pass!"


def _payload(current: str, new: str = NEW_PASSWORD) -> dict:
    return {
        "current_password": current,
        "new_password": new,
        "new_password_confirm": new,
    }


class TestChangePasswordSuccess:
    def test_updates_the_password(self, auth_client, user, password):
        response = auth_client.post(URL, _payload(password))

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)
        assert not user.check_password(password)

    def test_returns_a_fresh_token_pair(self, auth_client, user, password):
        body = auth_client.post(URL, _payload(password)).json()

        assert set(body) == {"access", "refresh", "detail"}

    def test_returned_tokens_are_usable(self, auth_client, api_client, user, password):
        body = auth_client.post(URL, _payload(password)).json()

        response = api_client.post(REFRESH_URL, {"refresh": body["refresh"]})

        assert response.status_code == 200

    def test_other_sessions_are_revoked(self, auth_client, api_client, user, password):
        other_device = str(RefreshToken.for_user(user))

        auth_client.post(URL, _payload(password))

        # A session opened before the change must not survive it.
        response = api_client.post(REFRESH_URL, {"refresh": other_device})
        assert response.status_code == 401

    def test_can_log_in_with_the_new_password(self, auth_client, api_client, user, password):
        auth_client.post(URL, _payload(password))

        response = api_client.post(
            reverse("api:login"), {"email": user.email, "password": NEW_PASSWORD}
        )

        assert response.status_code == 200


class TestChangePasswordValidation:
    def test_rejects_wrong_current_password(self, auth_client, user, password):
        response = auth_client.post(URL, _payload("Not-My-Passw0rd!"))

        assert response.status_code == 400
        assert "current_password" in response.json()["error"]["details"]
        user.refresh_from_db()
        assert user.check_password(password)

    def test_rejects_mismatched_confirmation(self, auth_client, password):
        response = auth_client.post(
            URL,
            {
                "current_password": password,
                "new_password": NEW_PASSWORD,
                "new_password_confirm": "Something-Else-1!",
            },
        )

        assert response.status_code == 400
        assert "new_password_confirm" in response.json()["error"]["details"]

    def test_rejects_reusing_the_current_password(self, auth_client, password):
        response = auth_client.post(URL, _payload(password, new=password))

        assert response.status_code == 400
        assert "new_password" in response.json()["error"]["details"]

    def test_rejects_weak_new_password(self, auth_client, password):
        response = auth_client.post(URL, _payload(password, new="password"))

        assert response.status_code == 400
        assert "new_password" in response.json()["error"]["details"]

    def test_requires_authentication(self, api_client, password):
        response = api_client.post(URL, _payload(password))

        assert response.status_code == 401
