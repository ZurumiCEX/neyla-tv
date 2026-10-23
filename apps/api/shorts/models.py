"""« Instant » (Shorts) : vidéos courtes verticales publiées par les streamers.

Les fichiers vivent dans la bibliothèque Bunny Stream (VOD) : upload direct
navigateur → Bunny (TUS signé), puis le webhook Bunny passe la vidéo en
« prête » à la fin de l'encodage.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Short(models.Model):
    class Status(models.TextChoices):
        UPLOADING = "uploading", "Envoi en cours"
        PROCESSING = "processing", "Encodage"
        READY = "ready", "Publiée"
        FAILED = "failed", "Échec"

    channel = models.ForeignKey(
        "channels_app.Channel", on_delete=models.CASCADE, related_name="shorts"
    )
    title = models.CharField(max_length=120)
    video_guid = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.UPLOADING, db_index=True
    )
    thumbnail_url = models.URLField(max_length=500, blank=True)
    playback_url = models.URLField(max_length=500, blank=True)
    duration_s = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    # Modération : une vidéo dépubliée n'apparaît plus dans le fil.
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_published", "-published_at"], name="shorts_feed_idx")
        ]

    def __str__(self) -> str:
        return f"short:{self.channel_id}:{self.title[:30]}"

    @property
    def is_visible(self) -> bool:
        return self.status == self.Status.READY and self.is_published


class ShortLike(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="short_likes"
    )
    short = models.ForeignKey(Short, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "short"], name="uniq_short_like")]

    def __str__(self) -> str:
        return f"like:{self.user_id}->{self.short_id}"
