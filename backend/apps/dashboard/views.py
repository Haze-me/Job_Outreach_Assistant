"""Dashboard endpoint."""

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.dashboard.serializers import DashboardSerializer
from apps.dashboard.services import build_dashboard


@extend_schema(
    summary="Dashboard statistics for the current user",
    description=(
        "Every counter shown on the dashboard, scoped to the requesting user "
        "and computed in a fixed number of database queries."
    ),
    responses={200: DashboardSerializer},
    tags=["dashboard"],
)
class DashboardView(APIView):
    """``GET /api/dashboard/``"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        stats = build_dashboard(user=request.user)
        return Response(DashboardSerializer(stats).data)
