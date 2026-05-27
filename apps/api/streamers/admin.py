from __future__ import annotations

from django.contrib import admin, messages

from . import services
from .models import StreamerApplication


@admin.register(StreamerApplication)
class StreamerApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "created_at", "decided_at", "decided_by")
    list_filter = ("status",)
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "decided_at", "decided_by")
    actions = ("approve_selected", "reject_selected")

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
                request,
                f"{approved} candidature(s) approuvée(s).",
                level=messages.SUCCESS,
            )

    @admin.action(description="Rejeter")
    def reject_selected(self, request, queryset):
        for application in queryset:
            services.reject_application(application, request.user)
        self.message_user(request, "Candidature(s) rejetée(s).", level=messages.SUCCESS)
