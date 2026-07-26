"""Dashboard response shape.

Declared explicitly rather than returning a bare dict so the figures appear in
the OpenAPI schema and the frontend can type against them.
"""

from rest_framework import serializers

from apps.applications.models import ApplicationStatus


class ApplicationsByStatusSerializer(serializers.Serializer):
    """One count per application status."""

    draft = serializers.IntegerField()
    sent = serializers.IntegerField()
    waiting = serializers.IntegerField()
    interview = serializers.IntegerField()
    offer = serializers.IntegerField()
    rejected = serializers.IntegerField()
    closed = serializers.IntegerField()


class DashboardSerializer(serializers.Serializer):
    """Every counter shown on the dashboard."""

    total_companies = serializers.IntegerField(help_text="Companies the user has added.")
    companies_scanned = serializers.IntegerField(
        help_text="Companies with at least one completed scan."
    )
    total_contacts = serializers.IntegerField(help_text="Contacts discovered across all scans.")
    favourite_contacts = serializers.IntegerField()

    total_applications = serializers.IntegerField()
    applications_sent = serializers.IntegerField(
        help_text="Applications past draft stage, whatever their current status."
    )
    pending_applications = serializers.IntegerField(
        help_text="Sent or waiting: no outcome recorded yet."
    )
    interviews = serializers.IntegerField()
    offers = serializers.IntegerField()
    rejections = serializers.IntegerField()
    drafts = serializers.IntegerField()

    applications_by_status = ApplicationsByStatusSerializer(
        help_text=f"Counts keyed by status: {', '.join(ApplicationStatus.values)}."
    )
