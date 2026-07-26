"""Tests for POST /api/auth/refresh/ and POST /api/auth/logout/."""

import pytest
from django.urls import reverse
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

pytestmark = pytest.mark.django_db

REFRESH_URL = reverse("api:token-refresh")
LOGOUT_URL = reverse("api:logout")
PROFILE_URL = reverse("api:profile")


class TestRefresh:
    def test_returns_a_new_access_token(self, api_client, refresh_token):
        response = api_client.post(REFRESH_URL, {"refresh": str(refresh_token)})

        assert response.status_code == 200
        assert "access" in response.json()

    def test_rotation_returns_a_new_refresh_token(self, api_client, refresh_token):
        response = api_client.post(REFRESH_URL, {"refresh": str(refresh_token)})

        assert response.json()["refresh"] != str(refresh_token)

    def test_used_refresh_token_is_blacklisted(self, api_client, refresh_token):
        api_client.post(REFRESH_URL, {"refresh": str(refresh_token)})

        # Replaying the same token must fail: a stolen refresh token is usable
        # at most once.
        replay = api_client.post(REFRESH_URL, {"refresh": str(refresh_token)})

        assert replay.status_code == 401

    def test_rotated_token_still_works(self, api_client, refresh_token):
        rotated = api_client.post(REFRESH_URL, {"refresh": str(refresh_token)}).json()["refresh"]

        response = api_client.post(REFRESH_URL, {"refresh": rotated})

        assert response.status_code == 200

    def test_rejects_garbage_token(self, api_client):
        response = api_client.post(REFRESH_URL, {"refresh": "not-a-token"})

        assert response.status_code == 401

    def test_refresh_requires_no_authentication_header(self, api_client, refresh_token):
        # The refresh token itself is the credential; an expired access token
        # must not block renewal.
        response = api_client.post(REFRESH_URL, {"refresh": str(refresh_token)})

        assert response.status_code == 200


class TestLogout:
    def test_blacklists_the_refresh_token(self, auth_client, user):
        refresh = str(RefreshToken.for_user(user))

        response = auth_client.post(LOGOUT_URL, {"refresh": refresh})

        assert response.status_code == 200
        assert response.json() == {"detail": "Signed out successfully."}
        assert BlacklistedToken.objects.filter(token__user=user).exists()

    def test_blacklisted_token_cannot_be_refreshed(self, auth_client, api_client, user):
        refresh = str(RefreshToken.for_user(user))
        auth_client.post(LOGOUT_URL, {"refresh": refresh})

        response = api_client.post(REFRESH_URL, {"refresh": refresh})

        assert response.status_code == 401

    def test_rejects_invalid_token(self, auth_client):
        response = auth_client.post(LOGOUT_URL, {"refresh": "not-a-token"})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "invalid_token"

    def test_double_logout_is_rejected(self, auth_client, user):
        refresh = str(RefreshToken.for_user(user))
        auth_client.post(LOGOUT_URL, {"refresh": refresh})

        response = auth_client.post(LOGOUT_URL, {"refresh": refresh})

        assert response.status_code == 400

    def test_requires_authentication(self, api_client, user):
        response = api_client.post(LOGOUT_URL, {"refresh": str(RefreshToken.for_user(user))})

        assert response.status_code == 401

    def test_requires_refresh_field(self, auth_client):
        response = auth_client.post(LOGOUT_URL, {})

        assert response.status_code == 400
        assert "refresh" in response.json()["error"]["details"]
