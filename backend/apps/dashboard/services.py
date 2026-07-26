"""Dashboard aggregation.

The dashboard is a read model over four apps. Every figure is computed by the
database in a fixed number of queries -- three, regardless of how many
companies, contacts, or applications the user has. Counting in Python would
turn the landing page into the slowest screen in the product.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Count, Q

from apps.applications.models import (
    PENDING_STATUSES,
    SENT_STATUSES,
    Application,
    ApplicationStatus,
)
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.crawler.models import ScanStatus

User = get_user_model()


def build_dashboard(*, user: User) -> dict:
    """Returns every counter the dashboard widgets display."""

    company_stats = Company.objects.filter(user=user).aggregate(
        total=Count("id", distinct=True),
        # A company counts as scanned once any scan has completed. `distinct`
        # matters: the join multiplies rows by scan count.
        scanned=Count(
            "id",
            filter=Q(scans__status=ScanStatus.COMPLETED),
            distinct=True,
        ),
    )

    contact_stats = Contact.objects.filter(user=user).aggregate(
        total=Count("id"),
        favourites=Count("id", filter=Q(is_favourite=True)),
    )

    # One pass over applications produces every status bucket.
    status_counts = Application.objects.filter(user=user).aggregate(
        total=Count("id"),
        sent=Count("id", filter=Q(status__in=SENT_STATUSES)),
        pending=Count("id", filter=Q(status__in=PENDING_STATUSES)),
        **{
            f"status_{value}": Count("id", filter=Q(status=value))
            for value, _label in ApplicationStatus.choices
        },
    )

    return {
        "total_companies": company_stats["total"],
        "companies_scanned": company_stats["scanned"],
        "total_contacts": contact_stats["total"],
        "favourite_contacts": contact_stats["favourites"],
        "total_applications": status_counts["total"],
        # "Sent" means anything past draft: an application at interview stage
        # was still sent. The by-status breakdown is included so the frontend
        # never has to re-derive this definition.
        "applications_sent": status_counts["sent"],
        "pending_applications": status_counts["pending"],
        "interviews": status_counts[f"status_{ApplicationStatus.INTERVIEW}"],
        "offers": status_counts[f"status_{ApplicationStatus.OFFER}"],
        "rejections": status_counts[f"status_{ApplicationStatus.REJECTED}"],
        "drafts": status_counts[f"status_{ApplicationStatus.DRAFT}"],
        "applications_by_status": {
            value: status_counts[f"status_{value}"] for value, _label in ApplicationStatus.choices
        },
    }
