from __future__ import annotations

from django.contrib import admin

from .models import BannedWord, Report


@admin.register(BannedWord)
class BannedWordAdmin(admin.ModelAdmin):
    list_display = ("word", "created_by", "created_at")
    search_fields = ("word",)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("reason", "status", "target_user", "channel", "reporter", "created_at")
    list_filter = ("status", "reason")
    search_fields = ("target_user__username", "reporter__username", "channel__slug")
    readonly_fields = (
        "reporter",
        "target_user",
        "channel",
        "message_id",
        "reason",
        "details",
        "created_at",
    )
