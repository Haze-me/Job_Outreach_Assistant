"""Uniform API error handling.

Every error the API returns has the same shape, so the frontend needs exactly
one branch for failures::

    {
      "error": {
        "code": "validation_error",
        "message": "Invalid input.",
        "details": {"website": ["Enter a valid URL."]}
      }
    }

``details`` is omitted when there is nothing structured to report.
"""

import logging
from typing import Any

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


class ServiceError(APIException):
    """Base class for failures raised by the service layer.

    Services raise these instead of returning error tuples, which keeps happy
    paths readable while still producing correct HTTP responses.
    """

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The request could not be completed."
    default_code = "service_error"


class ConflictError(ServiceError):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The resource is in a conflicting state."
    default_code = "conflict"


def _build_error_payload(detail: Any, code: str, message: str) -> dict:
    payload: dict[str, Any] = {"code": code, "message": message}
    # Field-level errors and non-scalar details are worth passing through;
    # a bare string is already carried by `message`.
    if isinstance(detail, (dict, list)):
        payload["details"] = detail
    return payload


def _default_message(detail: Any, fallback: str) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list) and detail:
        return str(detail[0])
    if isinstance(detail, dict):
        first = next(iter(detail.values()), None)
        if isinstance(first, list) and first:
            return str(first[0])
        if first is not None:
            return str(first)
    return fallback


def api_exception_handler(exc: Exception, context: dict) -> Response | None:
    """DRF ``EXCEPTION_HANDLER`` that normalises every failure response."""

    # Translate Django-native exceptions into their DRF equivalents so they get
    # the same envelope as everything else.
    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(detail=getattr(exc, "message_dict", None) or list(exc.messages))
    elif isinstance(exc, DjangoPermissionDenied):
        from rest_framework.exceptions import PermissionDenied

        exc = PermissionDenied()
    elif isinstance(exc, Http404):
        from rest_framework.exceptions import NotFound

        exc = NotFound()

    response = drf_exception_handler(exc, context)

    if response is None:
        # Unhandled: let Django produce the 500 (and DEBUG page) but make sure
        # the failure is recorded with request context.
        view = context.get("view")
        logger.exception("Unhandled exception in %s", view.__class__.__name__ if view else "view")
        return None

    detail = response.data
    code = getattr(exc, "default_code", "error")
    if isinstance(exc, ValidationError):
        code = "validation_error"
        message = "Invalid input."
    else:
        message = _default_message(detail, "Request failed.")

    # `detail` on a simple APIException duplicates the message; drop the wrapper.
    if isinstance(detail, dict) and set(detail.keys()) == {"detail"}:
        detail = detail["detail"]

    response.data = {"error": _build_error_payload(detail, code, message)}
    return response
