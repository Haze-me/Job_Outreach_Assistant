"""Serializers for scans and pages."""

from rest_framework import serializers

from apps.crawler.models import Page, Scan


class PageSerializer(serializers.ModelSerializer):
    """One page visited during a scan."""

    page_type_display = serializers.CharField(source="get_page_type_display", read_only=True)

    class Meta:
        model = Page
        fields = (
            "id",
            "url",
            "page_type",
            "page_type_display",
            "title",
            "status_code",
            "emails_found",
            "fetched_at",
        )
        read_only_fields = fields


class ScanSerializer(serializers.ModelSerializer):
    """Scan progress, as shown on the scan-progress screen."""

    company_name = serializers.CharField(source="company.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Scan
        fields = (
            "id",
            "company",
            "company_name",
            "status",
            "status_display",
            "progress_percent",
            "is_active",
            "target_url",
            "pages_discovered",
            "pages_scanned",
            "contacts_found",
            "started_at",
            "finished_at",
            "error_message",
            "created_at",
        )
        read_only_fields = fields


class ScanDetailSerializer(ScanSerializer):
    """Scan progress plus the pages visited so far."""

    pages = PageSerializer(many=True, read_only=True)

    class Meta(ScanSerializer.Meta):
        fields = (*ScanSerializer.Meta.fields, "pages")
        read_only_fields = fields
