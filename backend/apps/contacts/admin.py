from django.contrib import admin

from apps.contacts.models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("email", "classification", "company", "is_favourite", "created_at")
    list_filter = ("classification", "is_favourite", "created_at")
    search_fields = ("email", "company__name", "source_url", "user__email")
    readonly_fields = ("id", "source_page", "source_url", "created_at", "updated_at")
    autocomplete_fields = ("user", "company")
    date_hierarchy = "created_at"
    fieldsets = (
        (None, {"fields": ("id", "user", "company", "email", "classification")}),
        ("Provenance", {"fields": ("source_page", "source_url", "created_at")}),
        ("User annotations", {"fields": ("notes", "is_favourite")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("company", "user")
