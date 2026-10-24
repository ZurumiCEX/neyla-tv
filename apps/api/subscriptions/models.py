"""Abonnements de chaîne payés en Aura (mensuel) + avantages (perks)."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone

DEFAULT_BADGE_URL = ""  # le frontend rend un badge SVG par défaut si vide
DEFAULT_STICKERS: list[str] = []  # le frontend rend un pack de stickers par défaut si vide


class SubTier(models.Model):
    """Palier d'abonnement d'une chaîne (un actif par chaîne au MVP).

    Le streamer peut uploader son propre badge et ses stickers exclusifs. À défaut,
    le front affiche un pack par défaut.
    """

    channel = models.ForeignKey(
        "channels_app.Channel", on_delete=models.CASCADE, related_name="sub_tiers"
    )
    name = models.CharField(max_length=60, default="Abonnement")
    price_aura = models.PositiveIntegerField(default=100)
    perks = models.JSONField(default=list, blank=True)  # list[str] (texte libre)
    badge_url = models.URLField(blank=True, help_text="URL du badge abonné (PNG/SVG/WebP).")
    stickers_urls = models.JSONField(
        default=list, blank=True, help_text="Liste d'URL de stickers exclusifs (max 6 recommandé)."
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"tier:{self.channel_id}:{self.price_aura}"


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Actif"
        CANCELED = "canceled", "Annulé"
        EXPIRED = "expired", "Expiré"

    subscriber = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions"
    )
    channel = models.ForeignKey(
        "channels_app.Channel", on_delete=models.CASCADE, related_name="subscribers"
    )
    tier = models.ForeignKey(SubTier, on_delete=models.SET_NULL, null=True, blank=True)
    gifted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="gifted_subscriptions",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    started_at = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField()
    # Prix verrouillé à la souscription : les renouvellements facturent CE prix,
    # un changement de tarif du streamer ne vaut que pour les nouveaux abonnés.
    price_paid = models.PositiveIntegerField(default=0)
    # Annulation : l'accès reste ouvert jusqu'à la fin de la période payée.
    cancel_at_period_end = models.BooleanField(default=False)
    # Un abonnement offert ne se renouvelle pas (le destinataire n'a rien choisi).
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["subscriber", "channel"], name="uniq_subscription")
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"sub:{self.subscriber_id}->{self.channel_id}:{self.status}"

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE and self.current_period_end > timezone.now()

    @property
    def will_renew(self) -> bool:
        return self.is_active and self.auto_renew and not self.cancel_at_period_end


class SubscriptionGift(models.Model):
    """Historique permanent des abonnements offerts (le Subscription est écrasé)."""

    gifter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription_gifts_sent"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription_gifts_received",
    )
    channel = models.ForeignKey(
        "channels_app.Channel", on_delete=models.CASCADE, related_name="subscription_gifts"
    )
    price_aura = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["channel", "-created_at"], name="subgift_channel_idx")]

    def __str__(self) -> str:
        return f"gift {self.gifter_id}→{self.recipient_id} @{self.channel_id}"
