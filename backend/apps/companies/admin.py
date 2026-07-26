from django.contrib import admin

from apps.companies.models import Company, Note


class NoteInline(admin.TabularInline):
    model = Note
    extra = 0
    fields = ("content", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "website", "industry", "country", "user", "created_at")
    list_filter = ("industry", "country", "created_at")
    search_fields = ("name", "website", "industry", "country", "user__email")
    readonly_fields = ("id", "created_at", "updated_at")
    # A plain FK dropdown would load every user row.
    autocomplete_fields = ("user",)
    date_hierarchy = "created_at"
    inlines = [NoteInline]
    fieldsets = (
        (None, {"fields": ("id", "user", "name", "website")}),
        ("Classification", {"fields": ("industry", "country")}),
        ("Details", {"fields": ("description", "notes")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("__str__", "company", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content", "company__name", "user__email")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("user", "company")
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("company", "user")
