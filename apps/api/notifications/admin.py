from __future__ import annotations

from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "type", "actor", "read_at", "created_at")
    list_filter = ("type",)
    search_fields = ("recipient__username", "recipient__email")
    readonly_fields = ("recipient", "type", "actor", "payload", "read_at", "created_at")
