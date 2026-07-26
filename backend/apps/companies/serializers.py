"""Serializers for companies and notes."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models.functions import Lower
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.common.validators import normalize_website_url
from apps.companies.models import Company, Note


class LastScanSerializer(serializers.Serializer):
    """A summary of the company's most recent scan.

    Deliberately a plain ``Serializer`` reading duck-typed attributes rather
    than a ``ModelSerializer`` over ``crawler.Scan``: the companies app has no
    reason to import the crawler's models, and the reverse accessor is enough.
    """

    id = serializers.UUIDField(read_only=True)
    status = serializers.CharField(read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    pages_scanned = serializers.IntegerField(read_only=True)
    pages_discovered = serializers.IntegerField(read_only=True)
    contacts_found = serializers.IntegerField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    finished_at = serializers.DateTimeField(read_only=True)
    error_message = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)


class CompanyListSerializer(serializers.ModelSerializer):
    """Lean representation for the companies list.

    ``description`` and ``notes`` are omitted: they are unbounded text and
    would dominate the payload of a 20-item page for no benefit.
    """

    notes_count = serializers.IntegerField(read_only=True)
    date_added = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Company
        fields = (
            "id",
            "name",
            "website",
            "industry",
            "country",
            "notes_count",
            "date_added",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CompanySerializer(serializers.ModelSerializer):
    """Full company representation, used for detail reads and all writes."""

    notes_count = serializers.IntegerField(read_only=True)
    date_added = serializers.DateTimeField(source="created_at", read_only=True)
    # Declared as CharField rather than inheriting the model's URLField.
    # DRF runs a field's built-in validators *before* `validate_<field>`, so a
    # URLField would reject "example.com" for having no scheme -- exactly the
    # input `normalize_website_url` exists to accept and canonicalise.
    website = serializers.CharField(max_length=500)
    # Explicit defaults give PUT real replace semantics: an omitted optional
    # field is reset to empty. DRF skips defaults when `partial=True`, so PATCH
    # still leaves omitted fields untouched.
    industry = serializers.CharField(max_length=120, allow_blank=True, default="")
    country = serializers.CharField(max_length=120, allow_blank=True, default="")
    description = serializers.CharField(allow_blank=True, default="")
    notes = serializers.CharField(allow_blank=True, default="")
    last_scan = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = (
            "id",
            "name",
            "website",
            "industry",
            "country",
            "description",
            "notes",
            "notes_count",
            "last_scan",
            "date_added",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "notes_count",
            "last_scan",
            "date_added",
            "created_at",
            "updated_at",
        )

    @extend_schema_field(LastScanSerializer(allow_null=True))
    def get_last_scan(self, obj: Company) -> dict | None:
        """The most recent scan, or ``null`` if the company has never been scanned.

        This is what lets the scan-progress screen recover its scan id after a
        page reload: the id only otherwise exists in the response to the
        original POST. ``Scan.Meta.ordering`` puts the newest first.
        """
        scan = obj.scans.first()
        return LastScanSerializer(scan).data if scan is not None else None

    def validate_name(self, value: str) -> str:
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Enter a company name.")

        # The database constraint is the real guarantee; this check exists to
        # return a helpful field error instead of a bare conflict.
        user = self.context["request"].user
        duplicates = Company.objects.filter(user=user).annotate(lowered=Lower("name")).filter(
            lowered=name.lower()
        )
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("You have already added a company with this name.")
        return name

    def validate_website(self, value: str) -> str:
        try:
            return normalize_website_url(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc

    def validate_industry(self, value: str) -> str:
        return value.strip()

    def validate_country(self, value: str) -> str:
        return value.strip()


class NoteSerializer(serializers.ModelSerializer):
    """A single timestamped note attached to one of the user's companies."""

    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Note
        fields = ("id", "company", "company_name", "content", "created_at", "updated_at")
        read_only_fields = ("id", "company_name", "created_at", "updated_at")

    def validate_company(self, value: Company) -> Company:
        # Phrased as "not found" rather than "not yours": confirming that a
        # company id exists for someone else would leak information.
        if value.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Company not found.")
        return value

    def validate_content(self, value: str) -> str:
        content = value.strip()
        if not content:
            raise serializers.ValidationError("Enter some note content.")
        return content
