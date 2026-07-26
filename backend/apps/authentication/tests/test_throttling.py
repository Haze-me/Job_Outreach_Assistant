"""Rate limiting on the authentication endpoints.

Throttle rates are raised for the rest of the suite (see
``config.settings.test``); this module lowers them deliberately.

DRF binds ``SimpleRateThrottle.THROTTLE_RATES`` to the settings dict once at
import time, so ``override_settings`` cannot reach it -- the rates must be
patched on the class itself. In production this is a non-issue: the rates are
read from the environment when the process starts, which is exactly when they
are meant to be fixed.
"""

import pytest
from django.urls import reverse
from rest_framework.throttling import SimpleRateThrottle

pytestmark = pytest.mark.django_db

LOGIN_URL = reverse("api:login")
REGISTER_URL = reverse("api:register")
CHANGE_PASSWORD_URL = reverse("api:change-password")


@pytest.fixture
def strict_throttles(monkeypatch):
    monkeypatch.setattr(
        SimpleRateThrottle,
        "THROTTLE_RATES",
        {"auth_login": "3/min", "auth_register": "3/min", "auth_password": "3/min"},
    )


def test_repeated_failed_logins_are_throttled(api_client, user, strict_throttles):
    bad_credentials = {"email": user.email, "password": "Wrong-Passw0rd!"}

    statuses = [api_client.post(LOGIN_URL, bad_credentials).status_code for _ in range(4)]

    assert statuses[:3] == [401, 401, 401]
    assert statuses[3] == 429


def test_registration_is_throttled(api_client, strict_throttles):
    def register(index: int):
        return api_client.post(
            REGISTER_URL,
            {
                "email": f"user{index}@example.com",
                "password": "Str0ng-Passw0rd!",
                "password_confirm": "Str0ng-Passw0rd!",
            },
        )

    statuses = [register(i).status_code for i in range(4)]

    assert statuses[:3] == [201, 201, 201]
    assert statuses[3] == 429


def test_change_password_is_throttled(auth_client, password, strict_throttles):
    def attempt():
        return auth_client.post(
            CHANGE_PASSWORD_URL,
            {
                "current_password": "Wrong-Passw0rd!",
                "new_password": "An0ther-Str0ng-Pass!",
                "new_password_confirm": "An0ther-Str0ng-Pass!",
            },
        )

    statuses = [attempt().status_code for _ in range(4)]

    assert statuses[:3] == [400, 400, 400]
    assert statuses[3] == 429


def test_throttled_response_uses_the_standard_error_envelope(api_client, user, strict_throttles):
    bad_credentials = {"email": user.email, "password": "Wrong-Passw0rd!"}
    for _ in range(4):
        response = api_client.post(LOGIN_URL, bad_credentials)

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "throttled"


def test_profile_is_not_throttled(auth_client, strict_throttles):
    # Only views that declare a throttle_scope are limited; ordinary domain
    # endpoints must stay unaffected.
    statuses = [auth_client.get(reverse("api:profile")).status_code for _ in range(10)]

    assert set(statuses) == {200}
