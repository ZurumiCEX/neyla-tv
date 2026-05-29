from django.contrib import admin

from .models import Collaboration, Follow


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "followee", "created_at")
    search_fields = ("follower__username", "followee__username")
    date_hierarchy = "created_at"
    list_select_related = ("follower", "followee")
    list_per_page = 50
    ordering = ("-created_at",)


@admin.register(Collaboration)
class CollaborationAdmin(admin.ModelAdmin):
    list_display = ("inviter", "invitee", "status", "created_at", "responded_at")
    list_filter = ("status", "created_at")
    search_fields = ("inviter__username", "invitee__username")
    date_hierarchy = "created_at"
    list_select_related = ("inviter", "invitee")
    list_per_page = 50
    ordering = ("-created_at",)
