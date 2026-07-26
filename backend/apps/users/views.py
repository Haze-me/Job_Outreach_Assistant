"""Profile endpoint for the authenticated user."""

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.users.serializers import ProfileUpdateSerializer, UserSerializer

User = get_user_model()


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve the current user's profile",
        responses={200: UserSerializer},
        tags=["authentication"],
    ),
    put=extend_schema(
        summary="Replace the current user's profile",
        responses={200: ProfileUpdateSerializer},
        tags=["authentication"],
    ),
    patch=extend_schema(
        summary="Update the current user's profile",
        responses={200: ProfileUpdateSerializer},
        tags=["authentication"],
    ),
)
class ProfileView(generics.RetrieveUpdateAPIView):
    """Reads and updates the requesting user's own profile.

    There is no user id in the URL: the record is always ``request.user``, so
    there is no object to authorise against and no way to address someone
    else's profile.
    """

    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return ProfileUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user
