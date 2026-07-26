"""Object-level permissions.

Every domain record in this application belongs to exactly one job seeker.
Ownership is enforced in two places: querysets are filtered by owner (so
non-owned rows are invisible, returning 404 rather than leaking existence), and
these permission classes guard object access as defence in depth.
"""

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwner(permissions.BasePermission):
    """Grants access only when ``obj.user`` is the requesting user."""

    message = "You do not have permission to access this resource."
    owner_field = "user"

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        owner_field = getattr(view, "owner_field", self.owner_field)
        owner = obj
        for part in owner_field.split("__"):
            owner = getattr(owner, part, None)
            if owner is None:
                return False
        return owner == request.user


class IsOwnerOrReadOnly(IsOwner):
    """Read for any authenticated user, writes for the owner only."""

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return super().has_object_permission(request, view, obj)
