from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .models import Charity, CharityDonation, CharityEvent, PlatformEvent


@admin.register(Charity)
class CharityAdmin(admin.ModelAdmin):
    list_display = ("logo_preview", "name", "slug", "country", "is_active", "updated_at")
    list_display_links = ("logo_preview", "name")
    list_editable = ("is_active",)
    list_filter = ("is_active", "country")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)

    @admin.display(description="Logo")
    def logo_preview(self, obj):
        if obj.logo_url:
            return format_html(
                '<img src="{}" style="height:24px;width:24px;border-radius:5px;'
                'object-fit:cover" />',
                obj.logo_url,
            )
        return format_html('<span style="color:#888">—</span>')


@admin.register(CharityEvent)
class CharityEventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "theme",
        "starts_at",
        "ends_at",
        "floor_aura",
        "is_published",
        "total_aura_cached",
    )
    list_editable = ("is_published", "floor_aura")
    list_filter = ("is_published", "starts_at")
    search_fields = ("title", "slug", "theme")
    date_hierarchy = "starts_at"
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("beneficiaries",)
    readonly_fields = ("total_aura_cached", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("title", "slug", "theme", "is_published")}),
        ("Période", {"fields": ("starts_at", "ends_at", "floor_aura")}),
        ("Contenu", {"fields": ("description_md", "cover_url")}),
        ("Bénéficiaires", {"fields": ("beneficiaries",)}),
        ("Méta", {"fields": ("total_aura_cached", "created_at", "updated_at")}),
    )


@admin.register(CharityDonation)
class CharityDonationAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "event",
        "donor",
        "charity",
        "aura_amount",
        "is_anonymous",
    )
    list_filter = ("event", "charity", "is_anonymous", "created_at")
    search_fields = ("donor__username", "charity__name", "message")
    date_hierarchy = "created_at"
    list_select_related = ("event", "donor", "charity")
    readonly_fields = (
        "event",
        "donor",
        "charity",
        "aura_amount",
        "message",
        "is_anonymous",
        "created_at",
    )

    def has_add_permission(self, request):
        # Les dons ne se créent qu'à travers le service (débit ledger atomique).
        return False


@admin.register(PlatformEvent)
class PlatformEventAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "starts_at", "ends_at", "is_published", "featured")
    list_editable = ("is_published", "featured")
    list_filter = ("kind", "is_published", "featured", "starts_at")
    search_fields = ("title", "slug", "description_md")
    date_hierarchy = "starts_at"
    prepopulated_fields = {"slug": ("title",)}
