"""Création automatique d'une Channel (NON provisionnée) à l'inscription.

Le provisioning Cloudflare est déclenché à l'APPROBATION streamer (app `streamers`,
validation admin + quota), pas à l'inscription, afin de maîtriser les coûts.
On réserve seulement le slug = username pour garder la page publique cohérente.
"""

from __future__ import annotations

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Channel


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_channel_for_new_user(sender, instance, created, **kwargs):  # noqa: ARG001
    if not created:
        return
    Channel.objects.get_or_create(user=instance, defaults={"slug": instance.username})
