"""Follow user → user (un streamer suivi)."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following",
    )
    followee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["follower", "followee"], name="uniq_follow")]
        indexes = [models.Index(fields=["follower"]), models.Index(fields=["followee"])]

    def __str__(self) -> str:
        return f"{self.follower_id}→{self.followee_id}"
