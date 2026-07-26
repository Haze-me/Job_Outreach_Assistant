"""Operational endpoints that are not part of the domain API."""

from django.db import connection
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Liveness/readiness probe: confirms the process and its database."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(
        summary="Service health check",
        description="Returns the status of the API process and its database connection.",
        responses={200: dict, 503: dict},
        tags=["health"],
    )
    def get(self, request: Request) -> Response:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            database_ok = True
        except Exception:  # noqa: BLE001 - probe must never raise
            database_ok = False

        payload = {
            "status": "ok" if database_ok else "degraded",
            "database": "ok" if database_ok else "unavailable",
        }
        http_status = (
            status.HTTP_200_OK if database_ok else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response(payload, status=http_status)
