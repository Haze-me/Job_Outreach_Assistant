"""Abstract model building blocks reused across the domain apps.

These are deliberately abstract: they add no tables of their own and exist so
concrete models stay free of repeated bookkeeping fields.
"""

import uuid

from django.db import models


class TimeStampedModel(models.Model):
    """Adds automatic ``created_at`` / ``updated_at`` audit columns."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        get_latest_by = "created_at"


class UUIDPrimaryKeyModel(models.Model):
    """Uses a UUID primary key.

    Applied to records whose identifiers are exposed in URLs, so IDs cannot be
    enumerated to probe how much data other users hold.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class BaseModel(UUIDPrimaryKeyModel, TimeStampedModel):
    """The default base for domain models: UUID key plus timestamps."""

    class Meta:
        abstract = True
