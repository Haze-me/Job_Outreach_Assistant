"""Scanner endpoints."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.companies.models import Company
from apps.crawler.models import Scan
from apps.crawler.serializers import ScanDetailSerializer, ScanSerializer
from apps.crawler.services import scanner


@extend_schema(
    summary="Start a scan of a company's website",
    description=(
        "Validates the company's website, records a pending scan, and queues "
        "the crawl. Returns 202 immediately -- poll the status endpoint for "
        "progress. Returns 409 if a scan for this company is already running.\n\n"
        "Only publicly accessible pages are visited: robots.txt is honoured, "
        "requests are rate-limited, and the crawl is capped in both page count "
        "and depth."
    ),
    request=None,
    responses={202: ScanSerializer},
    tags=["scanner"],
)
class ScanCreateView(GenericAPIView):
    """``POST /api/scan/{company_id}``"""

    permission_classes = [IsAuthenticated]
    serializer_class = ScanSerializer

    def post(self, request: Request, company_id) -> Response:
        # Scoped to the requesting user, so another user's company id is
        # simply not found.
        company = get_object_or_404(Company, pk=company_id, user=request.user)

        scan = scanner.start_scan(user=request.user, company=company)
        return Response(
            self.get_serializer(scan).data,
            status=status.HTTP_202_ACCEPTED,
        )


@extend_schema(
    summary="Get the progress of a scan",
    description=(
        "Returns live counters plus every page visited so far. Poll this while "
        "`is_active` is true."
    ),
    responses={200: ScanDetailSerializer},
    tags=["scanner"],
)
class ScanStatusView(RetrieveAPIView):
    """``GET /api/scan/status/{scan_id}``"""

    permission_classes = [IsAuthenticated]
    serializer_class = ScanDetailSerializer
    lookup_url_kwarg = "scan_id"

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Scan.objects.none()
        return (
            Scan.objects.filter(user=self.request.user)
            .select_related("company")
            .prefetch_related("pages")
        )
