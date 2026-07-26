from django.contrib import admin

from apps.crawler.models import Page, Scan


class PageInline(admin.TabularInline):
    model = Page
    extra = 0
    fields = ("url", "page_type", "status_code", "emails_found", "fetched_at")
    readonly_fields = fields
    can_delete = False
    show_change_link = True


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "status",
        "pages_scanned",
        "pages_discovered",
        "contacts_found",
        "started_at",
        "finished_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("company__name", "target_url", "user__email")
    readonly_fields = (
        "id",
        "user",
        "company",
        "target_url",
        "task_id",
        "pages_discovered",
        "pages_scanned",
        "contacts_found",
        "started_at",
        "finished_at",
        "error_message",
        "created_at",
        "updated_at",
    )
    date_hierarchy = "created_at"
    inlines = [PageInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("company", "user")


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("url", "page_type", "status_code", "emails_found", "company", "fetched_at")
    list_filter = ("page_type", "status_code")
    search_fields = ("url", "title", "company__name")
    readonly_fields = ("id", "created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("company", "scan")
