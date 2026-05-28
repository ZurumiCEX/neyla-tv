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
    # Shadow ban : l'utilisateur peut poster (et voit ses messages) mais
    # personne d'autre ne les reçoit. La connexion n'est pas fermée.
    shadow = models.BooleanField(default=False)
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


class ChatIpBan(models.Model):
    """Ban d'une adresse IP sur une chaîne (bloque même les anonymes)."""

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="chat_ip_bans")
    ip = models.GenericIPAddressField()
    until = models.DateTimeField(null=True, blank=True)  # None = permanent
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="chat_ip_bans_issued",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["channel", "ip"], name="uniq_chatipban_per_channel_ip")
        ]
        indexes = [models.Index(fields=["channel", "ip"], name="chat_chatip_channel_idx")]

    def __str__(self) -> str:
        return f"ipban:{self.ip}@{self.channel_id}"

    def is_active(self) -> bool:
        return self.until is None or self.until > timezone.now()


class ChatUserIp(models.Model):
    """Dernière IP connue d'un utilisateur sur une chaîne (pour le ban IP ciblé)."""

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="chat_user_ips")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_user_ips"
    )
    ip = models.GenericIPAddressField()
    seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["channel", "user"], name="uniq_chatuserip_per_channel_user"
            )
        ]

    def __str__(self) -> str:
        return f"userip:{self.user_id}@{self.channel_id}={self.ip}"
