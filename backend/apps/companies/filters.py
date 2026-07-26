"""Query filters for companies and notes."""

from django_filters import rest_framework as filters

from apps.companies.models import Company, Note


class CompanyFilter(filters.FilterSet):
    """Filters matching the specification's search features.

    Industry and country are matched case-insensitively and exactly, so
    ``?country=Ireland`` and ``?country=ireland`` behave identically. Partial
    matching is what the ``?search=`` parameter is for.
    """

    industry = filters.CharFilter(lookup_expr="iexact")
    country = filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Company
        fields = ("industry", "country")


class NoteFilter(filters.FilterSet):
    """Notes are almost always read for one company at a time."""

    company = filters.UUIDFilter(field_name="company_id")

    class Meta:
        model = Note
        fields = ("company",)
