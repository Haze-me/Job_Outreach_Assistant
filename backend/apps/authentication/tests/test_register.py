"""Tests for POST /api/auth/register/."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

pytestmark = pytest.mark.django_db

URL = reverse("api:register")
VALID_PAYLOAD = {
    "email": "new.user@example.com",
    "password": "Str0ng-Passw0rd!",
    "password_confirm": "Str0ng-Passw0rd!",
    "first_name": "Grace",
    "last_name": "Hopper",
}


class TestRegisterSuccess:
    def test_creates_user_and_returns_tokens(self, api_client):
        response = api_client.post(URL, VALID_PAYLOAD)

        assert response.status_code == 201
        body = response.json()
        assert set(body) == {"access", "refresh", "user"}
        assert body["user"]["email"] == "new.user@example.com"
        assert body["user"]["full_name"] == "Grace Hopper"

        user = User.objects.get(email="new.user@example.com")
        assert user.check_password("Str0ng-Passw0rd!")

    def test_returned_access_token_works_immediately(self, api_client):
        access = api_client.post(URL, VALID_PAYLOAD).json()["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        profile = api_client.get(reverse("api:profile"))

        assert profile.status_code == 200
        assert profile.json()["email"] == "new.user@example.com"

    def test_email_is_normalised(self, api_client):
        response = api_client.post(URL, {**VALID_PAYLOAD, "email": "  MiXeD@Example.COM "})

        assert response.status_code == 201
        assert response.json()["user"]["email"] == "mixed@example.com"

    def test_names_are_optional(self, api_client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if "name" not in k}

        response = api_client.post(URL, payload)

        assert response.status_code == 201
        assert response.json()["user"]["first_name"] == ""

    def test_new_account_is_a_plain_job_seeker(self, api_client):
        api_client.post(URL, VALID_PAYLOAD)

        user = User.objects.get(email="new.user@example.com")
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False


class TestRegisterValidation:
    def test_rejects_duplicate_email_case_insensitively(self, api_client, user):
        response = api_client.post(URL, {**VALID_PAYLOAD, "email": user.email.upper()})

        assert response.status_code == 400
        assert "email" in response.json()["error"]["details"]
        assert User.objects.filter(email=user.email).count() == 1

    def test_rejects_mismatched_confirmation(self, api_client):
        response = api_client.post(
            URL, {**VALID_PAYLOAD, "password_confirm": "Different-Passw0rd!"}
        )

        assert response.status_code == 400
        assert "password_confirm" in response.json()["error"]["details"]
        assert not User.objects.filter(email=VALID_PAYLOAD["email"]).exists()

    @pytest.mark.parametrize(
        "password",
        ["short1!", "password", "12345678", "aaaaaaaa"],
        ids=["too-short", "too-common", "numeric-only", "too-common-repeat"],
    )
    def test_rejects_weak_passwords(self, api_client, password):
        response = api_client.post(
            URL, {**VALID_PAYLOAD, "password": password, "password_confirm": password}
        )

        assert response.status_code == 400
        assert "password" in response.json()["error"]["details"]

    def test_rejects_password_similar_to_email(self, api_client):
        payload = {
            **VALID_PAYLOAD,
            "email": "gracehopper@example.com",
            "password": "gracehopper@example.com",
            "password_confirm": "gracehopper@example.com",
        }

        response = api_client.post(URL, payload)

        assert response.status_code == 400
        assert "password" in response.json()["error"]["details"]

    def test_rejects_invalid_email_format(self, api_client):
        response = api_client.post(URL, {**VALID_PAYLOAD, "email": "not-an-email"})

        assert response.status_code == 400
        assert "email" in response.json()["error"]["details"]

    def test_rejects_missing_fields(self, api_client):
        response = api_client.post(URL, {})

        assert response.status_code == 400
        details = response.json()["error"]["details"]
        assert {"email", "password", "password_confirm"} <= set(details)

    def test_password_is_never_echoed_back(self, api_client):
        response = api_client.post(URL, VALID_PAYLOAD)

        assert "password" not in response.content.decode()
