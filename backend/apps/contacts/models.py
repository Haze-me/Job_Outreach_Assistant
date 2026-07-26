"""Contact model.

A contact is one publicly published email address found on a company's own
website, together with the page it was found on.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class ContactClassification(models.TextChoices):
    """The categories the specification asks contacts to be sorted into."""

    HR = "hr", _("HR")
    RECRUITMENT = "recruitment", _("Recruitment")
    CAREERS = "careers", _("Careers")
    TALENT = "talent", _("Talent")
    JOBS = "jobs", _("Jobs")
    SUPPORT = "support", _("Support")
    SALES = "sales", _("Sales")
    MEDIA = "media", _("Media")
    GENERAL = "general", _("General")
    UNKNOWN = "unknown", _("Unknown")


class Contact(BaseModel):
    """A discovered email address.

    Uniqueness is per company: the same address found on three pages of one
    site is one contact, but the same address legitimately appearing under two
    different companies stays two records.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contacts",
        verbose_name=_("owner"),
    )
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="contacts",
        verbose_name=_("company"),
    )

    email = models.EmailField(_("email address"), max_length=254)
    classification = models.CharField(
        _("classification"),
        max_length=20,
        choices=ContactClassification.choices,
        default=ContactClassification.UNKNOWN,
        db_index=True,
    )

    source_page = models.ForeignKey(
        "crawler.Page",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contacts",
        verbose_name=_("source page"),
    )
    # Kept as plain text as well as a foreign key: page rows belong to a scan,
    # and deleting an old scan must not erase the provenance of a contact the
    # user is still working with.
    source_url = models.URLField(_("source page URL"), max_length=1000, blank=True)

    notes = models.TextField(_("notes"), blank=True)
    is_favourite = models.BooleanField(_("favourite"), default=False, db_index=True)

    class Meta:
        verbose_name = _("contact")
        verbose_name_plural = _("contacts")
        ordering = ["-created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "email"],
                name="unique_contact_email_per_company",
                violation_error_message=_("This email is already saved for this company."),
            ),
        ]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="contact_user_recent_idx"),
            models.Index(fields=["company", "-created_at"], name="contact_company_recent_idx"),
            models.Index(fields=["user", "classification"], name="contact_user_class_idx"),
        ]

    def __str__(self) -> str:
        return self.email

    @property
    def date_discovered(self):
        """The specification's name for this value; ``created_at`` stores it."""
        return self.created_at
