"""Modèle Channel : une chaîne par streamer, mappée à un Live Input Cloudflare."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Channel(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="channel",
    )
    slug = models.SlugField(max_length=30, unique=True, db_index=True)
    title = models.CharField(max_length=140, blank=True)
    thumbnail_url = models.URLField(blank=True)
    banner_url = models.URLField(blank=True, default="")
    # Liens réseaux sociaux : {"twitter": "...", "youtube": "...", ...}
    # (clés validées contre une allowlist côté serializer).
    social_links = models.JSONField(default=dict, blank=True)
    # Tags libres de découverte (list[str], normalisés côté serializer).
    tags = models.JSONField(default=list, blank=True)
    # Jeton secret pour l'overlay d'alertes (browser source OBS, non authentifié).
    overlay_token = models.CharField(max_length=64, blank=True, db_index=True)
    # Ouvre/suspend la réception d'invitations de collaboration.
    collaborations_open = models.BooleanField(default=True)
    category = models.ForeignKey(
        "catalog.Game",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="channels",
    )

    # Cloudflare Stream Live Input.
    live_input_uid = models.CharField(max_length=64, blank=True, db_index=True)
    rtmps_url = models.CharField(max_length=200, blank=True)
    rtmps_key = models.CharField(max_length=200, blank=True)
    hls_playback_url = models.URLField(blank=True)

    is_live = models.BooleanField(default=False, db_index=True)
    last_live_started_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"channel:{self.slug}"

    @property
    def is_provisioned(self) -> bool:
        return bool(self.live_input_uid)


class StreamSession(models.Model):
    """Une session de diffusion : créée au passage live, clôturée au passage offline.

    Sert l'historique streamer (durée, pic viewers) et les analytics (Phase 7).
    Le titre/catégorie sont figés au démarrage (snapshot).
    """

    channel = models.ForeignKey(
        Channel,
        on_delete=models.CASCADE,
        related_name="sessions",
        db_index=True,
    )
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    peak_viewers = models.PositiveIntegerField(default=0)
    title_snapshot = models.CharField(max_length=140, blank=True)
    category_snapshot = models.ForeignKey(
        "catalog.Game",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"session:{self.channel.slug}:{self.started_at:%Y-%m-%d %H:%M}"

    @property
    def duration_seconds(self) -> int | None:
        if self.ended_at is None:
            return None
        return int((self.ended_at - self.started_at).total_seconds())
