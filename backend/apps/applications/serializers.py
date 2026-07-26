"""Serializers for job applications."""

from rest_framework import serializers

from apps.applications.models import Application, ApplicationStatus
from apps.companies.models import Company
from apps.contacts.models import Contact


class ApplicationSerializer(serializers.ModelSerializer):
    """Full representation, used for reads and writes.

    The specification's validation rules -- position, company and status are
    all required -- are enforced here rather than relying on model defaults, so
    an incomplete payload is rejected instead of silently becoming a draft.
    """

    company_name = serializers.CharField(source="company.name", read_only=True)
    company_website = serializers.CharField(source="company.website", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    is_sent = serializers.BooleanField(read_only=True)
    is_pending = serializers.BooleanField(read_only=True)

    status = serializers.ChoiceField(choices=ApplicationStatus.choices, required=True)
    position = serializers.CharField(max_length=255, required=True)
    # Explicit defaults give PUT real replace semantics; DRF skips defaults on
    # PATCH, so a partial update still leaves omitted fields alone.
    contact = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(), required=False, allow_null=True, default=None
    )
    contact_email = serializers.EmailField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    class Meta:
        model = Application
        fields = (
            "id",
            "company",
            "company_name",
            "company_website",
            "contact",
            "contact_email",
            "position",
            "application_date",
            "status",
            "status_display",
            "is_sent",
            "is_pending",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "company_name",
            "company_website",
            "status_display",
            "is_sent",
            "is_pending",
            "created_at",
            "updated_at",
        )

    def validate_company(self, value: Company) -> Company:
        # "Not found" rather than "not yours": confirming that a company id
        # exists for someone else would leak information.
        if value.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Company not found.")
        return value

    def validate_contact(self, value: Contact | None) -> Contact | None:
        if value is None:
            return None
        if value.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Contact not found.")
        return value

    def validate_position(self, value: str) -> str:
        position = value.strip()
        if not position:
            raise serializers.ValidationError("Enter the position applied for.")
        return position

    def validate_notes(self, value: str) -> str:
        return value.strip()

    def validate(self, attrs: dict) -> dict:
        # On PATCH the incoming data may name only one of the two, so fall back
        # to what is already stored.
        company = attrs.get("company") or getattr(self.instance, "company", None)
        contact = attrs.get("contact", getattr(self.instance, "contact", None))

        if contact is not None and company is not None and contact.company_id != company.pk:
            raise serializers.ValidationError(
                {"contact": "This contact belongs to a different company."}
            )

        # Recording the address on the application means it survives the
        # contact being deleted later.
        if contact is not None and not attrs.get("contact_email"):
            attrs["contact_email"] = contact.email

        return attrs
