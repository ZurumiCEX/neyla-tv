from __future__ import annotations

from django.contrib import admin, messages
from django.utils import timezone

from .models import BannedWord, Report


@admin.register(BannedWord)
class BannedWordAdmin(admin.ModelAdmin):
    list_display = ("word", "created_by", "created_at")
    search_fields = ("word",)
    ordering = ("word",)
    list_per_page = 100


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("reason", "status", "target_user", "channel", "reporter", "created_at")
    list_display_links = ("reason",)
    list_editable = ("status",)
    list_filter = ("status", "reason", "created_at")
    search_fields = ("target_user__username", "reporter__username", "channel__slug")
    date_hierarchy = "created_at"
    list_select_related = ("target_user", "channel", "reporter")
    list_per_page = 50
    ordering = ("-created_at",)
    actions = ("mark_reviewed", "mark_actioned", "mark_dismissed")
    readonly_fields = (
        "reporter",
        "target_user",
        "channel",
        "message_id",
        "reason",
        "details",
        "created_at",
    )

    def _set_status(self, request, queryset, status: str):
        n = queryset.update(status=status, reviewed_by=request.user, resolved_at=timezone.now())
        self.message_user(request, f"{n} signalement(s) → {status}.", level=messages.SUCCESS)

    @admin.action(description="Marquer comme examiné")
    def mark_reviewed(self, request, queryset):
        self._set_status(request, queryset, Report.Status.REVIEWED)

    @admin.action(description="Marquer comme actionné")
    def mark_actioned(self, request, queryset):
        self._set_status(request, queryset, Report.Status.ACTIONED)

    @admin.action(description="Rejeter")
    def mark_dismissed(self, request, queryset):
        self._set_status(request, queryset, Report.Status.DISMISSED)
