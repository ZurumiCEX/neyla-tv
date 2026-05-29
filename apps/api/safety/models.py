"""Modèles sécurité : anti-triche (RiskEvent) + anti-violation (ContentFlag)."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class RiskEvent(models.Model):
    """Signal anti-triche/anti-fraude détecté sur le comportement d'un utilisateur."""

    class Kind(models.TextChoices):
        TIP_VELOCITY = "tip_velocity", "Tips trop rapides"
        SELF_DEAL = "self_deal", "Auto-transaction"
        FOLLOW_VELOCITY = "follow_velocity", "Follows trop rapides"
        MULTI_ACCOUNT = "multi_account", "Multi-comptes (IP partagée)"
        VIEW_INFLATION = "view_inflation", "Gonflage de vues"
        SUB_ABUSE = "sub_abuse", "Abus d'abonnement"

    class Severity(models.IntegerChoices):
        LOW = 1, "Faible"
        MEDIUM = 2, "Moyen"
        HIGH = 3, "Élevé"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="risk_events"
    )
    kind = models.CharField(max_length=24, choices=Kind.choices, db_index=True)
    severity = models.PositiveSmallIntegerField(
        choices=Severity.choices, default=Severity.LOW, db_index=True
    )
    detail = models.JSONField(default=dict, blank=True)
    resolved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "kind"])]

    def __str__(self) -> str:
        return f"risk:{self.user_id}:{self.kind}:{self.severity}"


class ContentFlag(models.Model):
    """Signalement automatique de contenu (texte ou image) potentiellement illicite."""

    class Source(models.TextChoices):
        AVATAR = "avatar", "Avatar"
        BANNER = "banner", "Bannière"
        THUMBNAIL = "thumbnail", "Vignette"
        TITLE = "title", "Titre de stream"
        BIO = "bio", "Bio"
        TAG = "tag", "Tag"
        GAME_ART = "game_art", "Box art jeu"

    class Category(models.TextChoices):
        SAFE = "safe", "Sain"
        SEXUAL = "sexual", "Sexuel / pornographie"
        GORE = "gore", "Gore / violence"
        OTHER = "other", "Autre"

    class Status(models.TextChoices):
        PENDING = "pending", "À examiner"
        AUTO_BLOCKED = "auto_blocked", "Bloqué auto."
        APPROVED = "approved", "Approuvé"
        REJECTED = "rejected", "Rejeté"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="content_flags",
        null=True,
        blank=True,
    )
    channel = models.ForeignKey(
        "channels_app.Channel",
        on_delete=models.CASCADE,
        related_name="content_flags",
        null=True,
        blank=True,
    )
    source = models.CharField(max_length=16, choices=Source.choices)
    category = models.CharField(max_length=12, choices=Category.choices, db_index=True)
    confidence = models.FloatField(default=0.0)  # 0..1
    text = models.CharField(max_length=500, blank=True)
    url = models.URLField(max_length=500, blank=True)
    scores = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=14, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "category"])]

    def __str__(self) -> str:
        return f"flag:{self.source}:{self.category}:{self.status}"
