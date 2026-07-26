"""Serializers for discovered contacts."""

from rest_framework import serializers

from apps.contacts.models import Contact


class ContactSerializer(serializers.ModelSerializer):
    """Everything the contact list and detail screens display."""

    company_name = serializers.CharField(source="company.name", read_only=True)
    company_website = serializers.CharField(source="company.website", read_only=True)
    classification_display = serializers.CharField(
        source="get_classification_display", read_only=True
    )
    date_discovered = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Contact
        fields = (
            "id",
            "email",
            "classification",
            "classification_display",
            "company",
            "company_name",
            "company_website",
            "source_page",
            "source_url",
            "notes",
            "is_favourite",
            "date_discovered",
            "created_at",
            "updated_at",
        )
        # Contacts are produced by scans, never posted by clients. Only the
        # two user-owned annotations are writable.
        read_only_fields = tuple(f for f in fields if f not in ("notes", "is_favourite"))


class ContactUpdateSerializer(serializers.ModelSerializer):
    """The writable surface: notes and the favourite flag."""

    class Meta:
        model = Contact
        fields = ("notes", "is_favourite")

    def validate_notes(self, value: str) -> str:
        return value.strip()
