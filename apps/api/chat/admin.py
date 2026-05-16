from django.contrib import admin

from .models import ChatBan


@admin.register(ChatBan)
class ChatBanAdmin(admin.ModelAdmin):
    list_display = ("channel", "user", "until", "reason", "created_at", "created_by")
    list_filter = ("until",)
    search_fields = ("channel__slug", "user__username")
