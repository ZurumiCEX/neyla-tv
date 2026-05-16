from django.contrib import admin

from .models import Channel


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = (
        "slug",
        "user",
        "is_live",
        "is_provisioned",
        "last_live_started_at",
        "created_at",
    )
    list_filter = ("is_live",)
    search_fields = ("slug", "user__email", "user__username")
    readonly_fields = (
        "live_input_uid",
        "rtmps_url",
        "rtmps_key",
        "hls_playback_url",
        "created_at",
        "updated_at",
    )
