from __future__ import annotations

from django.contrib import admin

from .models import Subscription, SubTier


@admin.register(SubTier)
class SubTierAdmin(admin.ModelAdmin):
    list_display = ("channel", "name", "price_aura", "is_active", "updated_at")
    list_display_links = ("channel",)
    list_editable = ("price_aura", "is_active")
    list_filter = ("is_active",)
    search_fields = ("channel__slug",)
    list_select_related = ("channel",)
    list_per_page = 50


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("subscriber", "channel", "status", "current_period_end", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("subscriber__username", "channel__slug")
    date_hierarchy = "created_at"
    list_select_related = ("subscriber", "channel")
    list_per_page = 50
    ordering = ("-created_at",)
