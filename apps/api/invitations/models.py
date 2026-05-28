"""Codes d'invitation (parrainage). Le lien `invited_by` est porté par accounts.User."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Invite(models.Model):
    code = models.CharField(max_length=16, unique=True, db_index=True)
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invites"
    )
    max_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    @property
    def is_usable(self) -> bool:
        if self.used_count >= self.max_uses:
            return False
        return not (self.expires_at and self.expires_at <= timezone.now())
