"""Authentication endpoints.

Views are intentionally thin: they validate with a serializer, call a service,
and shape the response. No business rules live here.
"""

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.authentication import services
from apps.authentication.serializers import (
    AccessTokenResponseSerializer,
    ChangePasswordSerializer,
    DetailResponseSerializer,
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    TokenPairResponseSerializer,
)
from apps.users.serializers import UserSerializer


@extend_schema(
    summary="Register a new job seeker account",
    description=(
        "Creates an account and immediately returns a JWT pair, so the client "
        "does not have to hold the plaintext password in order to sign in "
        "straight afterwards."
    ),
    request=RegisterSerializer,
    responses={201: TokenPairResponseSerializer},
    tags=["authentication"],
    examples=[
        OpenApiExample(
            "Registration",
            value={
                "email": "jobseeker@example.com",
                "password": "Str0ng-Passw0rd!",
                "password_confirm": "Str0ng-Passw0rd!",
                "first_name": "Ada",
                "last_name": "Lovelace",
            },
            request_only=True,
        )
    ],
)
class RegisterView(GenericAPIView):
    """``POST /api/auth/register/``"""

    permission_classes = [AllowAny]
    authentication_classes: list = []
    serializer_class = RegisterSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = services.register_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
            first_name=serializer.validated_data.get("first_name", ""),
            last_name=serializer.validated_data.get("last_name", ""),
        )
        tokens = services.issue_tokens_for(user)

        return Response(
            {**tokens, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    summary="Sign in and obtain a JWT pair",
    request=LoginSerializer,
    responses={200: TokenPairResponseSerializer},
    tags=["authentication"],
)
class LoginView(TokenObtainPairView):
    """``POST /api/auth/login/``"""

    serializer_class = LoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"


@extend_schema(
    summary="Exchange a refresh token for a new access token",
    description=(
        "Rotation is enabled: the submitted refresh token is blacklisted and a "
        "new one is returned alongside the access token. Clients must store "
        "the new refresh token."
    ),
    responses={200: AccessTokenResponseSerializer},
    tags=["authentication"],
)
class RefreshView(TokenRefreshView):
    """``POST /api/auth/refresh/``"""

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"


@extend_schema(
    summary="Sign out of the current session",
    description=(
        "Blacklists the supplied refresh token so the session cannot be "
        "renewed. The current access token remains valid until it expires."
    ),
    request=LogoutSerializer,
    responses={200: DetailResponseSerializer},
    tags=["authentication"],
)
class LogoutView(GenericAPIView):
    """``POST /api/auth/logout/``"""

    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.logout(refresh_token=serializer.validated_data["refresh"])
        return Response({"detail": "Signed out successfully."}, status=status.HTTP_200_OK)


@extend_schema(
    summary="Change the current user's password",
    description=(
        "Verifies the current password, applies Django's password validators "
        "to the new one, then revokes every existing session and returns a "
        "fresh token pair for this device."
    ),
    request=ChangePasswordSerializer,
    responses={200: AccessTokenResponseSerializer},
    tags=["authentication"],
)
class ChangePasswordView(GenericAPIView):
    """``POST /api/auth/change-password/``"""

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_password"

    def post(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tokens = services.change_password(
            user=request.user,
            new_password=serializer.validated_data["new_password"],
        )
        return Response(
            {**tokens, "detail": "Password changed. All other sessions were signed out."},
            status=status.HTTP_200_OK,
        )
