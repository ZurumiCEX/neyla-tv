"""Drapeaux de plateforme (singleton key/value) : mode maintenance, etc."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class SiteFlag(models.Model):
    """Clé/valeur générique pour les flags de plateforme (maintenance, etc.)."""

    key = models.SlugField(max_length=40, unique=True)
    bool_value = models.BooleanField(default=False)
    text_value = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name = "Drapeau site"
        verbose_name_plural = "Drapeaux site"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.key}={self.bool_value}"


def maintenance_state() -> dict:
    """État courant de la maintenance (lecture rapide)."""
    flag = SiteFlag.objects.filter(key="maintenance").first()
    if flag is None:
        return {"active": False, "message": ""}
    return {"active": bool(flag.bool_value), "message": flag.text_value}
