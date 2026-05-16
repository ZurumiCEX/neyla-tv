"""Bans / timeouts du chat (persistés en DB pour survivre aux redémarrages)."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

from channels_app.models import Channel


class ChatBan(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="chat_bans")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_bans_received",
    )
    until = models.DateTimeField(null=True, blank=True)  # None = permanent
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="chat_bans_issued",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["channel", "user"], name="uniq_chatban_per_channel_user"
            )
        ]
        indexes = [models.Index(fields=["channel", "user"])]

    def __str__(self) -> str:
        return f"ban:{self.user_id}@{self.channel_id}"

    def is_active(self) -> bool:
        return self.until is None or self.until > timezone.now()
