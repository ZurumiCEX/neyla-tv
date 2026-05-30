from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .models import Achievement, UserAchievement


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("preview", "name", "key", "criteria_short", "is_active", "order")
    list_display_links = ("preview", "name")
    list_editable = ("is_active", "order")
    list_filter = ("is_active",)
    search_fields = ("key", "name", "description", "criteria")
    ordering = ("order", "id")
    fieldsets = (
        (None, {"fields": ("name", "key", "is_active", "order")}),
        ("Affichage", {"fields": ("description", "icon", "icon_url")}),
        (
            "Conditions de validation",
            {
                "fields": ("criteria",),
                "description": "Décris précisément l'action à réaliser pour débloquer ce succès "
                "(ex. « Faire 5 streams d'environ 5h sur une semaine »).",
            },
        ),
    )

    @admin.display(description="Icône")
    def preview(self, obj):
        if obj.icon_url:
            return format_html(
                '<img src="{}" style="height:24px;width:24px;border-radius:5px;'
                'object-fit:cover" />',
                obj.icon_url,
            )
        return format_html('<span style="font-size:20px">{}</span>', obj.icon)

    @admin.display(description="Conditions")
    def criteria_short(self, obj):
        text = obj.criteria or obj.description or ""
        return (text[:70] + "…") if len(text) > 70 else text


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "achievement", "awarded_at")
    list_filter = ("achievement", "awarded_at")
    search_fields = ("user__username", "achievement__key", "achievement__name")
    date_hierarchy = "awarded_at"
    autocomplete_fields = ("user", "achievement")
    readonly_fields = ("awarded_at",)
