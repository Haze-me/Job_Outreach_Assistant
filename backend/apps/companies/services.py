"""Company and note business logic."""

from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from apps.common.exceptions import ConflictError
from apps.companies.models import Company, Note

logger = logging.getLogger(__name__)
User = get_user_model()


class DuplicateCompanyError(ConflictError):
    default_detail = "You have already added a company with this name."
    default_code = "duplicate_company"


@transaction.atomic
def create_company(*, user: User, **fields: Any) -> Company:
    """Creates a company for ``user``.

    The serializer already rejects duplicate names, but two concurrent requests
    can both pass that check. The database constraint settles it, and the
    ``IntegrityError`` is translated into a clean 409 rather than a 500.
    """
    try:
        company = Company.objects.create(user=user, **fields)
    except IntegrityError as exc:
        raise DuplicateCompanyError() from exc

    logger.info("User %s added company %s", user.pk, company.pk)
    return company


@transaction.atomic
def update_company(*, company: Company, **fields: Any) -> Company:
    """Applies partial or full updates to an existing company."""
    for attr, value in fields.items():
        setattr(company, attr, value)
    try:
        company.save()
    except IntegrityError as exc:
        raise DuplicateCompanyError() from exc
    return company


@transaction.atomic
def delete_company(*, company: Company) -> None:
    """Deletes a company and everything hanging off it.

    Notes cascade today; scans, pages, contacts, and applications will cascade
    the same way once those models exist.
    """
    company_id = company.pk
    company.delete()
    logger.info("Deleted company %s", company_id)


@transaction.atomic
def create_note(*, user: User, company: Company, content: str) -> Note:
    """Adds a timestamped note to one of the user's companies."""
    return Note.objects.create(user=user, company=company, content=content)
