"""Catalogue de jeux/catégories. Curaté manuellement au MVP."""

from __future__ import annotations

from django.db import models


class Game(models.Model):
    class Group(models.TextChoices):
        GAMES = "games", "Jeux"
        IRL = "irl", "IRL"
        CHATTING = "chatting", "Discussions"
        MUSIC = "music", "Musique"
        CREATIVE = "creative", "Créativité"

    slug = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=120)
    box_art_url = models.URLField(blank=True)
    group = models.CharField(
        max_length=16, choices=Group.choices, default=Group.GAMES, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
