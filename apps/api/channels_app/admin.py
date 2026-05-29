from django.contrib import admin

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
        "live_input_uid",
        "rtmps_url",
        "rtmps_key",
        "hls_playback_url",
        "created_at",
        "updated_at",
    )
