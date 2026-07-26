"""Listing, search, filtering, ordering and pagination for /api/companies/."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.companies.models import Company

pytestmark = pytest.mark.django_db

LIST_URL = reverse("api:company-list")


@pytest.fixture
def catalogue(user):
    """A small, deliberately varied set of companies.

    ``created_at`` is set explicitly afterwards: ``auto_now_add`` reads the
    system clock, whose resolution is coarse enough on some platforms that four
    rows written in a loop share one timestamp, which would make any assertion
    about date ordering meaningless.
    """
    rows = [
        ("Acme Robotics", "Manufacturing", "Ireland"),
        ("Globex Software", "Software", "Ireland"),
        ("Initech Systems", "Software", "United Kingdom"),
        ("Umbrella Health", "Healthcare", "Germany"),
    ]
    companies = [
        Company.objects.create(
            user=user,
            name=name,
            website=f"https://{name.split()[0].lower()}.example.com",
            industry=industry,
            country=country,
        )
        for name, industry, country in rows
    ]

    base = timezone.now() - timedelta(days=len(companies))
    for offset, created in enumerate(companies):
        Company.objects.filter(pk=created.pk).update(created_at=base + timedelta(days=offset))
        created.refresh_from_db()

    return companies


def names(response) -> list[str]:
    return [row["name"] for row in response.json()["results"]]


class TestListing:
    def test_lists_only_your_own_companies(self, auth_client, catalogue, other_company):
        response = auth_client.get(LIST_URL)

        assert response.json()["count"] == 4
        assert "Not Yours Ltd" not in names(response)

    def test_uses_the_lean_list_serializer(self, auth_client, catalogue):
        row = auth_client.get(LIST_URL).json()["results"][0]

        # Unbounded text is excluded from list payloads.
        assert "description" not in row
        assert "notes" not in row
        assert "notes_count" in row

    def test_pagination_envelope(self, auth_client, catalogue):
        body = auth_client.get(LIST_URL, {"page_size": 2}).json()

        assert body["count"] == 4
        assert body["total_pages"] == 2
        assert body["page"] == 1
        assert body["page_size"] == 2
        assert len(body["results"]) == 2
        assert body["next"] is not None
        assert body["previous"] is None

    def test_page_size_is_capped(self, auth_client, catalogue):
        body = auth_client.get(LIST_URL, {"page_size": 5000}).json()

        assert body["page_size"] == 100

    def test_requires_authentication(self, api_client):
        assert api_client.get(LIST_URL).status_code == 401


class TestSearch:
    @pytest.mark.parametrize(
        ("term", "expected"),
        [
            ("acme", ["Acme Robotics"]),
            ("ROBOTICS", ["Acme Robotics"]),
            ("Healthcare", ["Umbrella Health"]),
            ("Ireland", ["Globex Software", "Acme Robotics"]),
            ("zzz-nothing", []),
        ],
    )
    def test_search_spans_name_industry_and_country(self, auth_client, catalogue, term, expected):
        response = auth_client.get(LIST_URL, {"search": term})

        assert sorted(names(response)) == sorted(expected)

    def test_search_is_scoped_to_the_owner(self, auth_client, catalogue, other_company):
        response = auth_client.get(LIST_URL, {"search": "Not Yours"})

        assert response.json()["count"] == 0


class TestFilters:
    def test_filter_by_industry(self, auth_client, catalogue):
        response = auth_client.get(LIST_URL, {"industry": "Software"})

        assert sorted(names(response)) == ["Globex Software", "Initech Systems"]

    def test_industry_filter_is_case_insensitive(self, auth_client, catalogue):
        response = auth_client.get(LIST_URL, {"industry": "sOfTwArE"})

        assert response.json()["count"] == 2

    def test_filter_by_country(self, auth_client, catalogue):
        response = auth_client.get(LIST_URL, {"country": "ireland"})

        assert sorted(names(response)) == ["Acme Robotics", "Globex Software"]

    def test_filters_combine(self, auth_client, catalogue):
        response = auth_client.get(LIST_URL, {"industry": "Software", "country": "Ireland"})

        assert names(response) == ["Globex Software"]

    def test_filter_and_search_combine(self, auth_client, catalogue):
        response = auth_client.get(LIST_URL, {"country": "Ireland", "search": "acme"})

        assert names(response) == ["Acme Robotics"]

    def test_unknown_filter_value_returns_empty(self, auth_client, catalogue):
        response = auth_client.get(LIST_URL, {"industry": "Aerospace"})

        assert response.json()["count"] == 0


class TestOrdering:
    def test_defaults_to_newest_first(self, auth_client, catalogue):
        response = auth_client.get(LIST_URL)

        assert names(response)[0] == "Umbrella Health"

    def test_order_by_name(self, auth_client, catalogue):
        response = auth_client.get(LIST_URL, {"ordering": "name"})

        assert names(response) == [
            "Acme Robotics",
            "Globex Software",
            "Initech Systems",
            "Umbrella Health",
        ]

    def test_order_by_name_descending(self, auth_client, catalogue):
        response = auth_client.get(LIST_URL, {"ordering": "-name"})

        assert names(response)[0] == "Umbrella Health"

    def test_invalid_ordering_field_is_ignored(self, auth_client, catalogue):
        response = auth_client.get(LIST_URL, {"ordering": "password"})

        assert response.status_code == 200
        assert response.json()["count"] == 4
