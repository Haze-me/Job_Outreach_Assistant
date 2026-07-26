"""Tests for the uniform API error envelope."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework.exceptions import NotAuthenticated, PermissionDenied, ValidationError

from apps.common.exceptions import ConflictError, ServiceError, api_exception_handler

CONTEXT: dict = {"view": None, "request": None}


def test_validation_error_returns_field_details():
    exc = ValidationError({"website": ["Enter a valid URL."]})

    response = api_exception_handler(exc, CONTEXT)

    assert response.status_code == 400
    assert response.data == {
        "error": {
            "code": "validation_error",
            "message": "Invalid input.",
            "details": {"website": ["Enter a valid URL."]},
        }
    }


def test_django_validation_error_is_translated():
    exc = DjangoValidationError({"name": ["This field cannot be blank."]})

    response = api_exception_handler(exc, CONTEXT)

    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
    assert response.data["error"]["details"] == {"name": ["This field cannot be blank."]}


def test_http_404_is_translated_to_not_found_envelope():
    response = api_exception_handler(Http404(), CONTEXT)

    assert response.status_code == 404
    assert response.data["error"]["code"] == "not_found"
    # A plain message needs no structured details.
    assert "details" not in response.data["error"]


def test_not_authenticated_envelope():
    response = api_exception_handler(NotAuthenticated(), CONTEXT)

    assert response.status_code == 401
    assert response.data["error"]["code"] == "not_authenticated"


def test_permission_denied_envelope():
    response = api_exception_handler(PermissionDenied(), CONTEXT)

    assert response.status_code == 403
    assert response.data["error"]["code"] == "permission_denied"


def test_service_error_envelope():
    response = api_exception_handler(ServiceError("Scan already running."), CONTEXT)

    assert response.status_code == 400
    assert response.data["error"] == {
        "code": "service_error",
        "message": "Scan already running.",
    }


def test_conflict_error_envelope():
    response = api_exception_handler(ConflictError(), CONTEXT)

    assert response.status_code == 409
    assert response.data["error"]["code"] == "conflict"


def test_unhandled_exception_is_left_to_django():
    class DummyView:
        pass

    assert api_exception_handler(RuntimeError("boom"), {"view": DummyView()}) is None
