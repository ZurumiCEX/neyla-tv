from __future__ import annotations

from django.contrib import admin

from .models import SiteFlag


@admin.register(SiteFlag)
class SiteFlagAdmin(admin.ModelAdmin):
    list_display = ("key", "bool_value", "text_value_short", "updated_at", "updated_by")
    list_editable = ("bool_value",)
    search_fields = ("key", "text_value")
    readonly_fields = ("updated_at", "updated_by")

    @admin.display(description="Message")
    def text_value_short(self, obj):
        v = obj.text_value or ""
        return (v[:60] + "…") if len(v) > 60 else v

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
