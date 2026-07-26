"""Query filters for job applications."""

from django_filters import rest_framework as filters

from apps.applications.models import (
    PENDING_STATUSES,
    SENT_STATUSES,
    Application,
    ApplicationStatus,
)


class ApplicationFilter(filters.FilterSet):
    """Covers the specification's application-status search feature."""

    company = filters.UUIDFilter(field_name="company_id")
    status = filters.ChoiceFilter(choices=ApplicationStatus.choices)
    applied_after = filters.DateFilter(field_name="application_date", lookup_expr="gte")
    applied_before = filters.DateFilter(field_name="application_date", lookup_expr="lte")
    # Convenience groupings so the dashboard tiles can link straight to a
    # filtered list without the frontend duplicating the status maths.
    is_sent = filters.BooleanFilter(method="filter_is_sent", label="Anything past draft")
    is_pending = filters.BooleanFilter(method="filter_is_pending", label="Sent, no outcome yet")

    class Meta:
        model = Application
        fields = ("company", "status")

    def filter_is_sent(self, queryset, name, value):
        if value is None:
            return queryset
        lookup = {"status__in": SENT_STATUSES}
        return queryset.filter(**lookup) if value else queryset.exclude(**lookup)

    def filter_is_pending(self, queryset, name, value):
        if value is None:
            return queryset
        lookup = {"status__in": PENDING_STATUSES}
        return queryset.filter(**lookup) if value else queryset.exclude(**lookup)
