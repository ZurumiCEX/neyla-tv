"""Annonces site (ticker + popup) gérées en back-office."""

from __future__ import annotations

from django.db import models
from django.utils import timezone


class SiteAnnouncement(models.Model):
    """Bannière/popup contrôlée par l'admin (visibilité, design, durée)."""

    class Level(models.TextChoices):
        INFO = "info", "Info"
        SUCCESS = "success", "Succès"
        WARNING = "warning", "Avertissement"
        CRITICAL = "critical", "Critique"

    class DisplayMode(models.TextChoices):
        TICKER = "ticker", "Ticker (défilant sous le header)"
        POPUP = "popup", "Pop-up (une fois par utilisateur)"
        BOTH = "both", "Ticker + pop-up"

    class Audience(models.TextChoices):
        ALL = "all", "Tous"
        STREAMERS = "streamers", "Streamers"
        VIEWERS = "viewers", "Spectateurs (non streamers)"
        ANONYMOUS = "anonymous", "Visiteurs anonymes"

    title = models.CharField(max_length=140)
    body = models.TextField(blank=True, help_text="Texte court. Markdown léger autorisé.")
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.INFO)
    display_mode = models.CharField(
        max_length=10, choices=DisplayMode.choices, default=DisplayMode.TICKER
    )
    audience = models.CharField(
        max_length=10, choices=Audience.choices, default=Audience.ALL, db_index=True
    )
    starts_at = models.DateTimeField(default=timezone.now, db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    dismissible = models.BooleanField(default=True)
    cta_label = models.CharField(max_length=40, blank=True)
    cta_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-starts_at"]
        verbose_name = "Annonce site"
        verbose_name_plural = "Annonces site"

    def __str__(self) -> str:  # pragma: no cover
        return self.title

    @property
    def is_live(self) -> bool:
        """Annonce publiée et dans sa fenêtre temporelle."""
        if not self.is_active:
            return False
        now = timezone.now()
        return self.starts_at <= now <= self.ends_at
