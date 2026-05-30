from __future__ import annotations

from django.contrib import admin, messages

from . import services
from .models import StreamerApplication


@admin.register(StreamerApplication)
class StreamerApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "score",
        "status",
        "community_size",
        "frequency",
        "has_streamed",
        "country",
        "created_at",
        "decided_by",
    )
    list_display_links = ("user",)
    list_editable = ("status",)
    list_filter = (
        "status",
        "has_streamed",
        "community_size",
        "frequency",
        "connection_quality",
        "country",
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "full_name",
        "main_games",
        "motivation",
        "tags",
    )
    date_hierarchy = "created_at"
    ordering = ("-score", "-created_at")
    list_per_page = 50
    list_select_related = ("user", "decided_by")
    actions = (
        "approve_selected",
        "reject_selected",
        "mark_under_review",
        "request_interview_selected",
    )
    readonly_fields = (
        "score",
        "created_at",
        "updated_at",
        "decided_at",
        "decided_by",
        "user",
    )
    fieldsets = (
        ("Décision", {"fields": ("user", "status", "score", "tags", "admin_notes")}),
        ("Identité", {"fields": ("full_name", "country", "primary_language")}),
        ("Profil gaming", {"fields": ("main_games", "content_categories")}),
        (
            "Motivation & vision",
            {"fields": ("motivation", "goals", "community_type", "why_select", "what_bring")},
        ),
        (
            "Expérience & régularité",
            {
                "fields": (
                    "has_streamed",
                    "platforms",
                    "community_size",
                    "frequency",
                    "avg_duration",
                )
            },
        ),
        ("Équipement", {"fields": ("setup", "connection_quality")}),
        ("Bonus", {"fields": ("intro_video_url", "setup_screenshot_url")}),
        (
            "Règles & dates",
            {
                "fields": (
                    "rules_accepted",
                    "rejection_reason",
                    "created_at",
                    "updated_at",
                    "decided_at",
                    "decided_by",
                )
            },
        ),
    )

    @admin.action(description="Approuver (provisionne la chaîne, respecte le quota/jour)")
    def approve_selected(self, request, queryset):
        approved = 0
        for application in queryset:
            try:
                services.approve_application(application, request.user)
                approved += 1
            except services.QuotaExceededError:
                self.message_user(
                    request,
                    "Quota quotidien d'approbations atteint — arrêt.",
                    level=messages.WARNING,
                )
                break
        if approved:
            self.message_user(
                request, f"{approved} candidature(s) approuvée(s).", level=messages.SUCCESS
            )

    @admin.action(description="Rejeter")
    def reject_selected(self, request, queryset):
        for application in queryset:
            services.reject_application(application, request.user)
        self.message_user(request, "Candidature(s) rejetée(s).", level=messages.SUCCESS)

    @admin.action(description="Marquer « en cours d'examen »")
    def mark_under_review(self, request, queryset):
        for application in queryset:
            services.set_under_review(application, request.user)
        self.message_user(request, "Candidature(s) en cours d'examen.", level=messages.SUCCESS)

    @admin.action(description="Demander un entretien")
    def request_interview_selected(self, request, queryset):
        for application in queryset:
            services.request_interview(application, request.user)
        self.message_user(request, "Entretien(s) demandé(s).", level=messages.SUCCESS)
