"""Succès (achievements) et leur attribution aux utilisateurs."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class Achievement(models.Model):
    key = models.CharField(
        max_length=50,
        unique=True,
        help_text="Identifiant technique stable (ex. hard_worker). Sans espaces.",
    )
    name = models.CharField(max_length=80, help_text="Désignation affichée (ex. « Hard worker »).")
    description = models.CharField(
        max_length=300, blank=True, help_text="Phrase courte affichée à l'utilisateur."
    )
    criteria = models.TextField(
        blank=True,
        help_text="Conditions pour valider le succès "
        "(ex. « Faire 5 streams d'environ 5h sur une semaine »).",
    )
    icon = models.CharField(
        max_length=8, default="🏆", help_text="Emoji par défaut si aucune icône image."
    )
    icon_url = models.URLField(
        blank=True,
        help_text="URL d'une icône image (en attendant l'upload Cloudflare R2). "
        "Prioritaire sur l'emoji.",
    )
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Décocher pour masquer le succès du catalogue."
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.name or self.key


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
