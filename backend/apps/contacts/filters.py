"""Query filters for contacts."""

from django_filters import rest_framework as filters

from apps.contacts.models import Contact, ContactClassification


class ContactFilter(filters.FilterSet):
    """Filters covering the specification's contact search features."""

    company = filters.UUIDFilter(field_name="company_id")
    classification = filters.ChoiceFilter(choices=ContactClassification.choices)
    is_favourite = filters.BooleanFilter()
    # "Show me anything recruitment-related" spans several categories, so it is
    # worth one parameter rather than four requests.
    recruitment_only = filters.BooleanFilter(
        method="filter_recruitment_only",
        label="Only recruitment-related classifications",
    )

    class Meta:
        model = Contact
        fields = ("company", "classification", "is_favourite")

    def filter_recruitment_only(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            classification__in=[
                ContactClassification.HR,
                ContactClassification.RECRUITMENT,
                ContactClassification.CAREERS,
                ContactClassification.TALENT,
                ContactClassification.JOBS,
            ]
        )
