"""Serializers for the authentication endpoints.

Validation lives here; state changes live in ``services``.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.users.serializers import UserSerializer

User = get_user_model()


def _validate_password_strength(password: str, user=None) -> str:
    """Runs Django's configured password validators, reported per-field."""
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(list(exc.messages)) from exc
    return password


class RegisterSerializer(serializers.Serializer):
    """Validates a new account and delegates creation to the service layer."""

    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        # Stored emails are always lower-cased, so an exact match is a reliable
        # case-insensitive check and can use the unique index.
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("An account with this email address already exists.")
        return email

    def validate_password(self, value: str) -> str:
        return _validate_password_strength(value)

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        # Re-run the validators with a user instance so the similarity check
        # can compare the password against the email and name.
        candidate = User(
            email=attrs["email"],
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc

        return attrs


class LoginSerializer(TokenObtainPairSerializer):
    """Email + password exchange for a JWT pair.

    Extends the SimpleJWT serializer rather than reimplementing it, so token
    creation, the active-user check, and ``last_login`` handling stay in one
    well-tested place.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Lets the frontend show the signed-in identity without an extra call.
        token["email"] = user.email
        return token

    def validate(self, attrs: dict) -> dict:
        # Emails are stored lower-cased, so normalise the input or a correct
        # password typed with different capitalisation would be rejected.
        username_field = self.username_field
        if attrs.get(username_field):
            attrs[username_field] = attrs[username_field].strip().lower()

        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class LogoutSerializer(serializers.Serializer):
    """Accepts the refresh token to invalidate."""

    refresh = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Validates a password change for the requesting user."""

    current_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_current_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Your current password is incorrect.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "Passwords do not match."}
            )
        if attrs["new_password"] == attrs["current_password"]:
            raise serializers.ValidationError(
                {"new_password": "The new password must be different from the current one."}
            )

        user = self.context["request"].user
        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)}) from exc

        return attrs


# ---------------------------------------------------------------------------
# Response-shape serializers (documentation only -- never used to parse input)
# ---------------------------------------------------------------------------
class TokenPairResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()


class AccessTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField(
        help_text="Returned because refresh-token rotation is enabled.",
    )


class DetailResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
