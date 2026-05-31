from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .models import SiteAnnouncement


@admin.register(SiteAnnouncement)
class SiteAnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        "preview",
        "title",
        "level",
        "display_mode",
        "audience",
        "starts_at",
        "ends_at",
        "is_active",
    )
    list_editable = ("is_active",)
    list_filter = ("is_active", "level", "display_mode", "audience")
    search_fields = ("title", "body")
    date_hierarchy = "starts_at"
    fieldsets = (
        (None, {"fields": ("title", "body", "is_active")}),
        ("Affichage", {"fields": ("level", "display_mode", "audience", "dismissible")}),
        ("Période", {"fields": ("starts_at", "ends_at")}),
        ("Call to action", {"fields": ("cta_label", "cta_url")}),
    )

    @admin.display(description="Aperçu")
    def preview(self, obj):
        bg = {
            "info": "#1e3a8a",
            "success": "#065f46",
            "warning": "#92400e",
            "critical": "#7f1d1d",
        }.get(obj.level, "#1f2937")
        return format_html(
            '<span style="display:inline-block;padding:4px 10px;border-radius:4px;'
            'background:{};color:#fff;font-weight:600;font-size:11px">{}</span>',
            bg,
            obj.level.upper(),
        )
