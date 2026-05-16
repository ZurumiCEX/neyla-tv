"""Modèle Channel : une chaîne par streamer, mappée à un Live Input Cloudflare."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Channel(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="channel",
    )
    slug = models.SlugField(max_length=30, unique=True, db_index=True)
    title = models.CharField(max_length=140, blank=True)
    thumbnail_url = models.URLField(blank=True)

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
