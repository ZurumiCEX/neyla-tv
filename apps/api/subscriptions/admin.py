from __future__ import annotations

from django.contrib import admin

from .models import Subscription, SubTier


@admin.register(SubTier)
class SubTierAdmin(admin.ModelAdmin):
    list_display = ("channel", "name", "price_aura", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("channel__slug",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("subscriber", "channel", "status", "current_period_end", "created_at")
    list_filter = ("status",)
    search_fields = ("subscriber__username", "channel__slug")
