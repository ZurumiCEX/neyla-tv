"""Succès (achievements) et leur attribution aux utilisateurs."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Achievement(models.Model):
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=8, default="🏆")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.key


class UserAchievement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="achievements"
    )
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name="+")
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-awarded_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "achievement"], name="uniq_user_achievement")
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.achievement_id}"
