"""Tâches Celery du domaine Channels."""

from __future__ import annotations

import logging

from celery import shared_task
from django.utils import timezone

from .bunny import BunnyStreamError, get_client
from .models import Channel
from .services import mark_live, mark_offline

logger = logging.getLogger(__name__)

# Nombre max de chaînes interrogées par passage (protège le quota API Bunny).
SYNC_BATCH_SIZE = 200


def sync_channel_status(channel: Channel, client=None) -> bool | None:
    """Aligne `is_live` sur l'état réel du flux Bunny. Retourne l'état, ou None si inconnu."""
    client = client or get_client()
    if client.is_fake or not channel.is_provisioned:
        return None
    try:
        status = client.get_live_status(channel.stream_id)
    except BunnyStreamError:
        logger.warning("sync_live_status: état indisponible pour %s", channel.slug, exc_info=True)
        return None
    Channel.objects.filter(pk=channel.pk).update(stream_checked_at=timezone.now())
    if status.is_live and mark_live(channel):
        from notifications.services import notify_followers_live

        notify_followers_live(channel)
    elif not status.is_live:
        mark_offline(channel)
    return status.is_live


@shared_task
def sync_live_status() -> int:
    """Polling Bunny : bascule live/offline (pas de webhook live documenté côté Bunny).

    Ordonné par dernière vérification pour répartir la charge sur les passages.
    Rattrape aussi les chaînes « coincées en live » si une déconnexion est ratée.
    """
    client = get_client()
    if client.is_fake:
        return 0
    channels = Channel.objects.exclude(stream_id="").order_by("-is_live", "stream_checked_at")[
        :SYNC_BATCH_SIZE
    ]
    checked = 0
    for channel in channels:
        if sync_channel_status(channel, client) is not None:
            checked += 1
    return checked
