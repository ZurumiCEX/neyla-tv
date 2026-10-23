from django.contrib import admin, messages

from .models import Short, ShortLike


@admin.register(Short)
class ShortAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "channel",
        "status",
        "is_published",
        "view_count",
        "like_count",
        "duration_s",
        "published_at",
    )
    list_filter = ("status", "is_published", "published_at")
    search_fields = ("title", "channel__slug", "video_guid")
    list_select_related = ("channel",)
    readonly_fields = ("video_guid", "view_count", "like_count", "created_at", "published_at")
    date_hierarchy = "created_at"
    actions = ("unpublish", "republish")

    @admin.action(description="Dépublier (modération)")
    def unpublish(self, request, queryset):
        n = queryset.update(is_published=False)
        self.message_user(request, f"{n} vidéo(s) dépubliée(s).", level=messages.SUCCESS)

    @admin.action(description="Republier")
    def republish(self, request, queryset):
        n = queryset.update(is_published=True)
        self.message_user(request, f"{n} vidéo(s) republiée(s).", level=messages.SUCCESS)


@admin.register(ShortLike)
class ShortLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "short", "created_at")
    search_fields = ("user__username", "short__title")
    list_select_related = ("user", "short")
