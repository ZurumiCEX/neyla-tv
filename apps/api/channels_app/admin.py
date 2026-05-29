from datetime import timedelta

from django.contrib import admin
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.safestring import mark_safe

from config.admin_widgets import labeled_chart, stat_grid

from .models import Channel, StreamSession


class StreamSessionInline(admin.TabularInline):
    """Historique des sessions de diffusion, en lecture seule, sur la chaîne."""

    model = StreamSession
    extra = 0
    can_delete = False
    ordering = ("-started_at",)
    fields = ("started_at", "ended_at", "peak_viewers", "title_snapshot")
    readonly_fields = fields
    show_change_link = True
    verbose_name_plural = "Sessions récentes"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(StreamSession)
class StreamSessionAdmin(admin.ModelAdmin):
    list_display = ("channel", "started_at", "ended_at", "peak_viewers")
    list_filter = ("started_at",)
    search_fields = ("channel__slug",)
    date_hierarchy = "started_at"
    list_select_related = ("channel",)
    list_per_page = 50
    ordering = ("-started_at",)
    readonly_fields = (
        "channel",
        "started_at",
        "ended_at",
        "peak_viewers",
        "title_snapshot",
        "category_snapshot",
    )


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "user",
        "is_live",
        "collaborations_open",
        "category",
        "last_live_started_at",
        "created_at",
    )
    list_display_links = ("slug",)
    list_editable = ("is_live", "collaborations_open")
    list_filter = ("is_live", "collaborations_open", "category")
    search_fields = ("slug", "user__email", "user__username")
    date_hierarchy = "created_at"
    list_select_related = ("user", "category")
    list_per_page = 50
    ordering = ("-created_at",)
    inlines = (StreamSessionInline,)
    readonly_fields = (
        "activity_summary",
        "live_input_uid",
        "rtmps_url",
        "rtmps_key",
        "hls_playback_url",
        "created_at",
        "updated_at",
    )

    @admin.display(description="Synthèse d'activité")
    def activity_summary(self, obj: Channel):
        if obj is None or obj.pk is None:
            return "—"
        sessions = obj.sessions.all()
        ended = sessions.filter(ended_at__isnull=False).only("started_at", "ended_at")
        hours = round(sum((s.ended_at - s.started_at).total_seconds() for s in ended) / 3600, 1)
        followers = obj.user.followers.count()
        tips = obj.tips.aggregate(n=Count("id"), aura=Sum("aura_amount"))
        grid = stat_grid(
            [
                ("Sessions", sessions.count()),
                ("Heures diffusées", hours),
                ("Abonnés", followers),
                ("Tips reçus", tips["n"] or 0),
                ("Aura reçus", tips["aura"] or 0),
            ]
        )
        chart = labeled_chart("Sessions / jour (30j)", self._sessions_series(obj), "#5D1C6A")
        return mark_safe(f"{grid}{chart}")  # noqa: S308 — fragments internes déjà sûrs

    @staticmethod
    def _sessions_series(obj: Channel, days: int = 30) -> list[int]:
        now = timezone.now()
        since = now - timedelta(days=days - 1)
        start = timezone.localtime(since).date()
        buckets = {(start + timedelta(days=i)).isoformat(): 0 for i in range(days)}
        qs = obj.sessions.filter(started_at__gte=since).only("started_at")
        for s in qs:
            key = timezone.localtime(s.started_at).date().isoformat()
            if key in buckets:
                buckets[key] += 1
        return list(buckets.values())
