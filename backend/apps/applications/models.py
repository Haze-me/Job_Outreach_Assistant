"""Job application model.

One record per application a job seeker sends to a company. The status field
tracks it through the lifecycle the specification defines, from an unsent draft
to a closed outcome.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class ApplicationStatus(models.TextChoices):
    """The lifecycle of an application, in the order it normally progresses."""

    DRAFT = "draft", _("Draft")
    SENT = "sent", _("Sent")
    WAITING = "waiting", _("Waiting")
    INTERVIEW = "interview", _("Interview")
    OFFER = "offer", _("Offer")
    REJECTED = "rejected", _("Rejected")
    CLOSED = "closed", _("Closed")


# Everything except a draft has actually been sent. Grouped here rather than
# inline so the dashboard and the API cannot drift apart on the definition.
SENT_STATUSES = (
    ApplicationStatus.SENT,
    ApplicationStatus.WAITING,
    ApplicationStatus.INTERVIEW,
    ApplicationStatus.OFFER,
    ApplicationStatus.REJECTED,
    ApplicationStatus.CLOSED,
)

# Sent, but no outcome yet.
PENDING_STATUSES = (ApplicationStatus.SENT, ApplicationStatus.WAITING)


class Application(BaseModel):
    """An application sent to one company for one position."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name=_("owner"),
    )
    company = models.ForeignKey(
        "companies.Company",
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name=_("company"),
    )

    contact = models.ForeignKey(
        "contacts.Contact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
        verbose_name=_("contact"),
        help_text=_("The discovered contact this was sent to, when there is one."),
    )
    # Kept alongside the foreign key so the record still says who was written
    # to after a contact is removed, and so an address that was never
    # discovered by a scan can still be recorded.
    contact_email = models.EmailField(_("contact email"), max_length=254, blank=True)

    position = models.CharField(_("position applied for"), max_length=255)
    application_date = models.DateField(_("application date"), default=timezone.localdate)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
        db_index=True,
    )
    notes = models.TextField(_("notes"), blank=True)

    class Meta:
        verbose_name = _("application")
        verbose_name_plural = _("applications")
        ordering = ["-application_date", "-created_at", "id"]
        indexes = [
            models.Index(fields=["user", "-application_date"], name="application_user_date_idx"),
            models.Index(fields=["user", "status"], name="application_user_status_idx"),
            models.Index(fields=["company", "-created_at"], name="application_company_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.position} @ {self.company_id} ({self.status})"

    @property
    def is_sent(self) -> bool:
        return self.status in SENT_STATUSES

    @property
    def is_pending(self) -> bool:
        return self.status in PENDING_STATUSES
