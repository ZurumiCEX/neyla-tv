"""Catalogue de jeux/catégories. Curaté manuellement au MVP."""

from __future__ import annotations

from django.db import models


class Game(models.Model):
    slug = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=120)
    box_art_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
