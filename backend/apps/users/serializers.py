"""Serializers for the user resource."""

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Read-only representation of the authenticated user.

    Used inside auth responses and as the GET payload for the profile
    endpoint. Deliberately exposes no permission flags beyond ``is_staff``.
    """

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "is_active",
            "is_staff",
            "date_joined",
        )
        read_only_fields = fields


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Writable profile fields.

    ``email`` is intentionally read-only: it is the login identifier, and
    changing it without a verification step would let a typo lock the account
    out permanently. The specification lists no email-delivery capability, so
    email changes are out of scope for the MVP.
    """

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "date_joined",
        )
        read_only_fields = ("id", "email", "full_name", "date_joined")

    def validate_first_name(self, value: str) -> str:
        return value.strip()

    def validate_last_name(self, value: str) -> str:
        return value.strip()
