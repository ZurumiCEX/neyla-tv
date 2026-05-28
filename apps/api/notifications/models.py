"""Notifications in-app (live d'une chaîne suivie, nouveau follower, candidature)."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        LIVE_STARTED = "live_started", "Live démarré"
        NEW_FOLLOWER = "new_follower", "Nouveau follower"
        APPLICATION_DECIDED = "application_decided", "Candidature traitée"
        SUBSCRIPTION = "subscription", "Nouvel abonné"
        TIP_RECEIVED = "tip_received", "Tip reçu"
        ACHIEVEMENT = "achievement", "Succès débloqué"
        SUPPORT_MESSAGE = "support_message", "Message du support"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
    )
    type = models.CharField(max_length=32, choices=Type.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    payload = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "read_at"], name="notif_recipient_read_idx")]

    def __str__(self) -> str:
        return f"{self.type} → {self.recipient_id}"


class NotificationPreference(models.Model):
    """Préférence d'un utilisateur pour un type de notification (absent = activé)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_prefs"
    )
    type = models.CharField(max_length=32, choices=Notification.Type.choices)
    enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "type"], name="uniq_notif_pref")]

    def __str__(self) -> str:
        return f"pref:{self.user_id}:{self.type}={self.enabled}"


class PushSubscription(models.Model):
    """Abonnement Web Push (VAPID) d'un appareil/navigateur."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_subscriptions"
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"push:{self.user_id}:{self.endpoint[:40]}"
