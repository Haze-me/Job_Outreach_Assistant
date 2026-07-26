from django.contrib import admin

from apps.applications.models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("position", "company", "status", "application_date", "contact_email", "user")
    list_filter = ("status", "application_date")
    search_fields = ("position", "company__name", "contact_email", "notes", "user__email")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("user", "company")
    date_hierarchy = "application_date"
    fieldsets = (
        (None, {"fields": ("id", "user", "company", "position", "status")}),
        ("Contact", {"fields": ("contact", "contact_email")}),
        ("Details", {"fields": ("application_date", "notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("company", "user", "contact")
