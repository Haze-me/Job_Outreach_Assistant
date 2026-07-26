"""The job seeker account model.

The MVP has a single role (job seeker), so no role field exists yet. Django's
``is_staff``/``is_superuser`` flags remain available for admin access only.
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """A registered job seeker, identified by email address.

    Email replaces Django's ``username`` because the product has no concept of
    a separate handle, and a second identifier would only be another thing to
    keep unique and in sync.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(
        _("email address"),
        unique=True,
        help_text=_("Used to sign in. Stored lower-cased."),
    )
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)

    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Deactivate instead of deleting to preserve related records."),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into the Django admin site."),
    )

    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    # Email is already the username field, so it must not be repeated here.
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.email

    def clean(self) -> None:
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email).lower()

    def save(self, *args, **kwargs):
        # Normalise on every write so lookups by email are reliably exact.
        self.email = self.email.lower().strip()
        return super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def get_full_name(self) -> str:
        return self.full_name or self.email

    def get_short_name(self) -> str:
        return self.first_name or self.email.split("@")[0]
