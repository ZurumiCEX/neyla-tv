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


class Collaboration(models.Model):
    """Lien de collaboration entre deux créateurs (« Streamer ensemble »)."""

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        ACCEPTED = "accepted", "Acceptée"
        DECLINED = "declined", "Refusée"

    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collaborations_sent"
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collaborations_received"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["inviter", "invitee"], name="uniq_collaboration")
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"collab:{self.inviter_id}<->{self.invitee_id}:{self.status}"
