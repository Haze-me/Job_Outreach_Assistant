"""Company and Note models.

The specification lists ``Notes`` both as a *field* on a company and as its own
table. Both exist here, and they serve different purposes:

* ``Company.notes`` -- a free-text scratchpad attached to the company record
  itself, edited in place alongside the other company fields.
* ``Note``          -- individual, timestamped entries forming a running log
  ("Applied through careers email", "Recruiter replied"), each added and
  deleted independently.

There is no separate ``notes`` app in the specification's backend structure, so
``Note`` lives with the company it belongs to.
"""

from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class Company(BaseModel):
    """A company the job seeker is tracking.

    Every company belongs to exactly one user. Two different job seekers may
    both track "Acme Ltd" -- uniqueness is therefore scoped per user, not
    global.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="companies",
        verbose_name=_("owner"),
    )

    name = models.CharField(_("company name"), max_length=255)
    website = models.URLField(
        _("website URL"),
        max_length=500,
        help_text=_("Normalised on save, e.g. 'Example.com/' becomes 'https://example.com'."),
    )
    industry = models.CharField(_("industry"), max_length=120, blank=True)
    country = models.CharField(_("country"), max_length=120, blank=True)
    description = models.TextField(_("description"), blank=True)
    notes = models.TextField(
        _("notes"),
        blank=True,
        help_text=_("Free-text notes stored on the company record itself."),
    )

    class Meta:
        verbose_name = _("company")
        verbose_name_plural = _("companies")
        # Newest first: the list a job seeker wants is what they just added.
        ordering = ["-created_at", "name"]
        constraints = [
            # Case-insensitive so "Acme" and "acme" cannot both be added.
            # Enforced in the database, which is the only place that holds
            # under concurrent requests.
            models.UniqueConstraint(
                Lower("name"),
                "user",
                name="unique_company_name_per_user",
                violation_error_message=_("You have already added a company with this name."),
            ),
        ]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="company_user_recent_idx"),
            models.Index(fields=["user", "industry"], name="company_user_industry_idx"),
            models.Index(fields=["user", "country"], name="company_user_country_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def date_added(self):
        """The specification's name for this value; ``created_at`` stores it."""
        return self.created_at


class Note(BaseModel):
    """A timestamped note attached to a company.

    ``user`` duplicates ``company.user``. The denormalisation is deliberate: it
    lets every note query filter on a single indexed column instead of joining
    through companies, and it keeps the ownership-scoping mixin uniform across
    every domain model.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name=_("owner"),
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        # `notes` is taken by Company's own text field.
        related_name="note_entries",
        verbose_name=_("company"),
    )
    content = models.TextField(_("content"))

    class Meta:
        verbose_name = _("note")
        verbose_name_plural = _("notes")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="note_user_recent_idx"),
            models.Index(fields=["company", "-created_at"], name="note_company_recent_idx"),
        ]

    def __str__(self) -> str:
        preview = self.content[:50]
        suffix = "..." if len(self.content) > 50 else ""
        return f"{self.company_id}: {preview}{suffix}"
