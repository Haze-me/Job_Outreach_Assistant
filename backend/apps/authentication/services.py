"""Authentication business logic.

Views stay thin and serializers stay focused on validation; anything that
changes state or coordinates more than one object lives here. Every function
takes keyword-only arguments so call sites are self-documenting.
"""

from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.exceptions import ServiceError

logger = logging.getLogger(__name__)
User = get_user_model()


class InvalidTokenError(ServiceError):
    default_detail = "The provided token is invalid or has already been used."
    default_code = "invalid_token"


def issue_tokens_for(user: User) -> dict[str, str]:
    """Mints a fresh access/refresh pair for ``user``.

    Creating the refresh token also records an ``OutstandingToken`` row (the
    blacklist app is installed), which is what makes logout and
    revoke-everything possible.
    """
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


@transaction.atomic
def register_user(
    *,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
) -> User:
    """Creates a new job seeker account.

    Uniqueness is also enforced by the serializer; the database constraint is
    the real guarantee and protects against two concurrent registrations
    racing past the same validation check.
    """
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
    )
    logger.info("Registered new user %s", user.pk)
    return user


def logout(*, refresh_token: str) -> None:
    """Blacklists a single refresh token, ending that one session.

    Access tokens are stateless and stay valid until they expire (15 minutes by
    default); blacklisting the refresh token is what prevents the session from
    being renewed.
    """
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except TokenError as exc:
        # Already blacklisted, expired, or malformed -- all indistinguishable
        # to the caller by design, so no information leaks about token state.
        raise InvalidTokenError() from exc


def revoke_all_sessions(*, user: User) -> int:
    """Blacklists every outstanding refresh token belonging to ``user``.

    Returns the number of tokens revoked. Used after a password change so a
    stolen session cannot outlive the credential it was obtained with.
    """
    revoked = 0
    for outstanding in OutstandingToken.objects.filter(user=user).iterator():
        _, created = BlacklistedToken.objects.get_or_create(token=outstanding)
        if created:
            revoked += 1
    logger.info("Revoked %s session(s) for user %s", revoked, user.pk)
    return revoked


@transaction.atomic
def change_password(*, user: User, new_password: str) -> dict[str, str]:
    """Sets a new password, revokes all existing sessions, and re-issues tokens.

    Revoking every session is the safe default: if the old password leaked, any
    session opened with it dies immediately. A fresh pair is returned so the
    user who *initiated* the change is not logged out of the device they are
    using -- other devices must sign in again.
    """
    user.set_password(new_password)
    user.save(update_fields=["password", "updated_at"])

    revoke_all_sessions(user=user)
    return issue_tokens_for(user)
