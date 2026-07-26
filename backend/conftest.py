"""Shared pytest fixtures for the whole backend test suite."""

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

DEFAULT_PASSWORD = "Str0ng-Passw0rd!"


@pytest.fixture(autouse=True)
def _clear_cache():
    """Throttle counters live in the cache; leaking them across tests is flaky."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def password() -> str:
    return DEFAULT_PASSWORD


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="jobseeker@example.com",
        password=DEFAULT_PASSWORD,
        first_name="Ada",
        last_name="Lovelace",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email="someone.else@example.com",
        password=DEFAULT_PASSWORD,
    )


@pytest.fixture
def company(user):
    from apps.companies.models import Company

    return Company.objects.create(
        user=user,
        name="Acme Robotics",
        website="https://acme-robotics.example.com",
        industry="Manufacturing",
        country="Ireland",
        description="Industrial automation.",
    )


@pytest.fixture
def other_company(other_user):
    """A company owned by somebody else -- used to prove isolation."""
    from apps.companies.models import Company

    return Company.objects.create(
        user=other_user,
        name="Not Yours Ltd",
        website="https://not-yours.example.com",
    )


@pytest.fixture
def note(user, company):
    from apps.companies.models import Note

    return Note.objects.create(
        user=user,
        company=company,
        content="Applied through careers email.",
    )


@pytest.fixture
def refresh_token(user) -> RefreshToken:
    return RefreshToken.for_user(user)


@pytest.fixture
def auth_client(api_client, user) -> APIClient:
    """An APIClient carrying a valid access token for ``user``."""
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client
