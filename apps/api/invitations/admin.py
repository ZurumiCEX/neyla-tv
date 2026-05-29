from __future__ import annotations

from django.contrib import admin

from .models import Invite


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ("code", "inviter", "used_count", "max_uses", "expires_at", "created_at")
    search_fields = ("code", "inviter__username")
    date_hierarchy = "created_at"
    list_select_related = ("inviter",)
    list_per_page = 50
    ordering = ("-created_at",)
