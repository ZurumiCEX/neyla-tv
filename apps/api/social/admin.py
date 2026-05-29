from django.contrib import admin

from .models import Collaboration, Follow


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "followee", "created_at")
    search_fields = ("follower__username", "followee__username")


@admin.register(Collaboration)
class CollaborationAdmin(admin.ModelAdmin):
    list_display = ("inviter", "invitee", "status", "created_at", "responded_at")
    list_filter = ("status",)
    search_fields = ("inviter__username", "invitee__username")
