"""Company and note endpoints."""

from django.db.models import Count, QuerySet
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import Serializer

from apps.common.mixins import MultiSerializerMixin, OwnerScopedQuerySetMixin
from apps.common.permissions import IsOwner
from apps.companies import services
from apps.companies.filters import CompanyFilter, NoteFilter
from apps.companies.models import Company, Note
from apps.companies.serializers import (
    CompanyListSerializer,
    CompanySerializer,
    NoteSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List the current user's companies",
        parameters=[
            OpenApiParameter(
                "search",
                str,
                description="Partial, case-insensitive match on name, industry, or country.",
            ),
            OpenApiParameter(
                "ordering",
                str,
                description=(
                    "Sort field. One of: name, created_at, industry, country. "
                    "Prefix with '-' to reverse. Defaults to -created_at."
                ),
            ),
        ],
        tags=["companies"],
    ),
    create=extend_schema(summary="Add a company", tags=["companies"]),
    retrieve=extend_schema(summary="Retrieve a company", tags=["companies"]),
    update=extend_schema(summary="Replace a company", tags=["companies"]),
    partial_update=extend_schema(summary="Update a company", tags=["companies"]),
    destroy=extend_schema(summary="Delete a company", tags=["companies"]),
)
class CompanyViewSet(OwnerScopedQuerySetMixin, MultiSerializerMixin, viewsets.ModelViewSet):
    """Full CRUD over the companies belonging to the requesting user.

    The queryset is scoped by owner before anything else runs, so another
    user's company is simply not addressable -- every operation on it answers
    404.
    """

    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = CompanySerializer
    serializer_classes = {"list": CompanyListSerializer}
    filterset_class = CompanyFilter
    search_fields = ("name", "industry", "country")
    ordering_fields = ("name", "created_at", "updated_at", "industry", "country")
    # `name` breaks ties. Timestamps are not guaranteed unique -- the system
    # clock resolution on Windows is coarse enough that rows saved in the same
    # request can share a created_at -- and an unstable sort would let the same
    # row appear on two pages, or on neither.
    ordering = ("-created_at", "name")

    queryset = Company.objects.all()

    def get_queryset(self) -> QuerySet[Company]:
        # Counting in the database avoids one extra query per row on the list.
        return super().get_queryset().annotate(notes_count=Count("note_entries", distinct=True))

    def perform_create(self, serializer: Serializer) -> None:
        company = services.create_company(
            user=self.request.user, **serializer.validated_data
        )
        serializer.instance = company

    def perform_update(self, serializer: Serializer) -> None:
        company = services.update_company(
            company=serializer.instance, **serializer.validated_data
        )
        serializer.instance = company

    def perform_destroy(self, instance: Company) -> None:
        services.delete_company(company=instance)


@extend_schema_view(
    list=extend_schema(
        summary="List the current user's notes",
        parameters=[
            OpenApiParameter(
                "company",
                str,
                description="Return only notes attached to this company id.",
            )
        ],
        tags=["notes"],
    ),
    create=extend_schema(summary="Add a note to a company", tags=["notes"]),
    retrieve=extend_schema(summary="Retrieve a note", tags=["notes"]),
    update=extend_schema(summary="Replace a note", tags=["notes"]),
    partial_update=extend_schema(summary="Update a note", tags=["notes"]),
    destroy=extend_schema(summary="Delete a note", tags=["notes"]),
)
class NoteViewSet(OwnerScopedQuerySetMixin, viewsets.ModelViewSet):
    """Timestamped notes, filterable to a single company."""

    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = NoteSerializer
    filterset_class = NoteFilter
    search_fields = ("content",)
    ordering_fields = ("created_at", "updated_at")
    # `id` is arbitrary but stable -- see the note on CompanyViewSet.ordering.
    ordering = ("-created_at", "id")

    queryset = Note.objects.select_related("company").all()
