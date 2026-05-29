from django.contrib import admin

from .models import ContentFlag, RiskEvent


@admin.register(RiskEvent)
class RiskEventAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "kind", "severity", "resolved", "created_at")
    list_filter = ("kind", "severity", "resolved", "created_at")
    search_fields = ("user__username",)
    autocomplete_fields = ("user",)
    date_hierarchy = "created_at"
    list_per_page = 50
    ordering = ("-created_at",)
    list_editable = ("resolved",)
    list_display_links = ("id",)
    readonly_fields = ("created_at",)


@admin.register(ContentFlag)
class ContentFlagAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "source",
        "category",
        "status",
        "confidence",
        "user",
        "channel",
        "created_at",
    )
    list_filter = ("source", "category", "status", "created_at")
    search_fields = ("user__username", "channel__slug", "text")
    date_hierarchy = "created_at"
    list_per_page = 50
    ordering = ("-created_at",)
    list_editable = ("status",)
    list_display_links = ("id",)
    readonly_fields = ("created_at", "resolved_at")
