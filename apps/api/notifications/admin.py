from __future__ import annotations

from django.contrib import admin

from .models import Notification, NotificationPreference, PushSubscription


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "type", "actor", "read_at", "created_at")
    list_filter = ("type",)
    search_fields = ("recipient__username", "recipient__email")
    readonly_fields = ("recipient", "type", "actor", "payload", "read_at", "created_at")


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "enabled")
    list_filter = ("type", "enabled")
    search_fields = ("user__username",)


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "endpoint", "created_at")
    search_fields = ("user__username", "endpoint")
    readonly_fields = ("user", "endpoint", "p256dh", "auth", "created_at")
