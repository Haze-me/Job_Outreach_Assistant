"""Tests for the operational health endpoint."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_health_check_is_public_and_reports_ok():
    response = APIClient().get(reverse("api:health-check"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
