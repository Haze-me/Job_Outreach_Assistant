"""Reusable viewset behaviour."""

from django.db.models import QuerySet
from rest_framework.serializers import Serializer


class OwnerScopedQuerySetMixin:
    """Restricts a viewset's queryset to rows owned by the requesting user.

    Filtering at the queryset level (rather than only checking permissions on a
    fetched object) means another user's record is indistinguishable from one
    that does not exist -- the API answers 404, never 403, so it never confirms
    that some other user owns a given id.
    """

    owner_field = "user"

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        # drf-spectacular introspects viewsets without a real request.
        if getattr(self, "swagger_fake_view", False) or not self.request:
            return queryset.none()
        user = self.request.user
        if not user or not user.is_authenticated:
            return queryset.none()
        return queryset.filter(**{self.owner_field: user})

    def perform_create(self, serializer: Serializer) -> None:
        serializer.save(**{self.owner_field: self.request.user})


class MultiSerializerMixin:
    """Selects a serializer per action via a ``serializer_classes`` mapping.

    Keeps list payloads lean while detail and write actions use richer
    serializers, without branching inside ``get_serializer_class``.
    """

    serializer_classes: dict[str, type[Serializer]] = {}

    def get_serializer_class(self) -> type[Serializer]:
        return self.serializer_classes.get(self.action, super().get_serializer_class())
