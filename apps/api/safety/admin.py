from django.contrib import admin

from .models import ContentFlag, RiskEvent


@admin.register(RiskEvent)
class RiskEventAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "kind", "severity", "resolved", "created_at")
    list_filter = ("kind", "severity", "resolved")
    search_fields = ("user__username",)
    autocomplete_fields = ("user",)
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
    list_filter = ("source", "category", "status")
    search_fields = ("user__username", "channel__slug", "text")
    readonly_fields = ("created_at", "resolved_at")
