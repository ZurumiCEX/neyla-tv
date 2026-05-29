from django.contrib import admin

from .models import ChatBan, ChatIpBan, ChatUserIp


@admin.register(ChatBan)
class ChatBanAdmin(admin.ModelAdmin):
    list_display = ("channel", "user", "until", "shadow", "reason", "created_at", "created_by")
    list_filter = ("shadow", "until")
    search_fields = ("channel__slug", "user__username")


@admin.register(ChatIpBan)
class ChatIpBanAdmin(admin.ModelAdmin):
    list_display = ("channel", "ip", "until", "reason", "created_at", "created_by")
    search_fields = ("channel__slug", "ip")


@admin.register(ChatUserIp)
class ChatUserIpAdmin(admin.ModelAdmin):
    list_display = ("channel", "user", "ip", "seen_at")
    search_fields = ("channel__slug", "user__username", "ip")
    readonly_fields = ("channel", "user", "ip", "seen_at")
