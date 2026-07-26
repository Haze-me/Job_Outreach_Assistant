"""Contact endpoints."""

from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.common.mixins import OwnerScopedQuerySetMixin
from apps.common.permissions import IsOwner
from apps.contacts.filters import ContactFilter
from apps.contacts.models import Contact
from apps.contacts.serializers import ContactSerializer, ContactUpdateSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List discovered contacts",
        parameters=[
            OpenApiParameter(
                "search", str, description="Partial match on email, notes, or company name."
            ),
            OpenApiParameter("company", str, description="Only contacts for this company id."),
            OpenApiParameter("classification", str, description="Exact classification value."),
            OpenApiParameter("is_favourite", bool, description="Only favourites when true."),
            OpenApiParameter(
                "recruitment_only",
                bool,
                description="Only HR, recruitment, careers, talent and jobs contacts.",
            ),
        ],
        tags=["contacts"],
    ),
    retrieve=extend_schema(summary="Retrieve a contact", tags=["contacts"]),
    update=extend_schema(summary="Update a contact's notes or favourite flag", tags=["contacts"]),
    partial_update=extend_schema(
        summary="Update a contact's notes or favourite flag", tags=["contacts"]
    ),
)
class ContactViewSet(
    OwnerScopedQuerySetMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Read and annotate contacts discovered by scans.

    There is no create or delete: contacts exist because a scan found them on a
    public page. Users may add notes and mark favourites, which is the whole
    writable surface the specification describes.
    """

    permission_classes = [IsAuthenticated, IsOwner]
    filterset_class = ContactFilter
    search_fields = ("email", "notes", "company__name")
    ordering_fields = ("created_at", "email", "classification")
    ordering = ("-created_at", "id")

    queryset = Contact.objects.select_related("company", "source_page").all()

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return ContactUpdateSerializer
        return ContactSerializer
