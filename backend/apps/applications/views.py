"""Job application endpoints."""

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.applications.filters import ApplicationFilter
from apps.applications.models import Application
from apps.applications.serializers import ApplicationSerializer
from apps.common.mixins import OwnerScopedQuerySetMixin
from apps.common.permissions import IsOwner


@extend_schema_view(
    list=extend_schema(
        summary="List job applications",
        parameters=[
            OpenApiParameter(
                "search",
                str,
                description="Partial match on position, company name, contact email, or notes.",
            ),
            OpenApiParameter("status", str, description="Exact application status."),
            OpenApiParameter("company", str, description="Only applications to this company id."),
            OpenApiParameter("is_sent", bool, description="Anything past draft."),
            OpenApiParameter("is_pending", bool, description="Sent, with no outcome yet."),
            OpenApiParameter("applied_after", str, description="ISO date, inclusive."),
            OpenApiParameter("applied_before", str, description="ISO date, inclusive."),
        ],
        tags=["applications"],
    ),
    create=extend_schema(summary="Record a job application", tags=["applications"]),
    retrieve=extend_schema(summary="Retrieve an application", tags=["applications"]),
    update=extend_schema(summary="Replace an application", tags=["applications"]),
    partial_update=extend_schema(summary="Update an application", tags=["applications"]),
    destroy=extend_schema(summary="Delete an application", tags=["applications"]),
)
class ApplicationViewSet(OwnerScopedQuerySetMixin, viewsets.ModelViewSet):
    """Full CRUD over the requesting user's applications."""

    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = ApplicationSerializer
    filterset_class = ApplicationFilter
    search_fields = ("position", "company__name", "contact_email", "notes")
    ordering_fields = ("application_date", "created_at", "status", "position")
    # `id` breaks ties: application_date is a date, so same-day rows would
    # otherwise sort unstably and could repeat or vanish across pages.
    ordering = ("-application_date", "-created_at", "id")

    queryset = Application.objects.select_related("company", "contact").all()
