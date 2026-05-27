from __future__ import annotations

from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "target_type", "target_id", "created_at")
    list_filter = ("action",)
    search_fields = ("action", "actor__username", "target_id")
    readonly_fields = ("actor", "action", "target_type", "target_id", "meta", "created_at")
