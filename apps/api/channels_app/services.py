"""Services métier des chaînes (provisionnement, rotation, live on/off)."""

from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from .bunny import BunnyStreamError, get_client
from .models import Channel, StreamSession

logger = logging.getLogger(__name__)

_STREAM_FIELDS = ["stream_id", "ingest_url", "stream_key", "playback_url"]


def _store_stream(channel: Channel, live) -> None:
    channel.stream_id = live.stream_id
    channel.ingest_url = live.ingest_url
    channel.stream_key = live.stream_key
    channel.playback_url = live.playback_url


@transaction.atomic
def provision_channel(channel: Channel) -> Channel:
    """Crée le live stream Bunny et stocke les identifiants. Idempotent."""
    if channel.is_provisioned:
        return channel
    live = get_client().create_live_stream(label=f"channel:{channel.slug}")
    _store_stream(channel, live)
    channel.save(update_fields=[*_STREAM_FIELDS, "updated_at"])
    return channel


def rotate_stream_key(channel: Channel) -> Channel:
    """Crée un nouveau live stream PUIS supprime l'ancien (force OBS à reconfigurer).

    Ordre « créer avant supprimer » : si la création échoue, la chaîne garde son
    ancien flux et reste provisionnée.
    """
    client = get_client()
    old_id = channel.stream_id
    live = client.create_live_stream(label=f"channel:{channel.slug}")
    with transaction.atomic():
        _store_stream(channel, live)
        channel.save(update_fields=[*_STREAM_FIELDS, "updated_at"])
        mark_offline(channel)
    if old_id:
        try:
            client.delete_live_stream(old_id)
        except BunnyStreamError:
            logger.exception("rotate_stream_key: suppression de l'ancien flux %s échouée", old_id)
    return channel


def mark_live(channel: Channel) -> bool:
    """Bascule la chaîne en live + ouvre une StreamSession. True si changement."""
    if channel.is_live:
        return False
    channel.is_live = True
    channel.last_live_started_at = timezone.now()
    channel.save(update_fields=["is_live", "last_live_started_at", "updated_at"])
    StreamSession.objects.create(
        channel=channel,
        title_snapshot=channel.title,
        category_snapshot=channel.category,
    )
    from gamification.services import check_and_award

    check_and_award(channel.user, "first_stream")
    return True


def mark_offline(channel: Channel) -> bool:
    """Bascule la chaîne offline + clôt la session ouverte. True si changement."""
    if not channel.is_live:
        return False
    channel.is_live = False
    channel.save(update_fields=["is_live", "updated_at"])
    StreamSession.objects.filter(channel=channel, ended_at__isnull=True).update(
        ended_at=timezone.now()
    )
    return True


def record_session_peak(channel_id: int, viewers: int) -> None:
    """Met à jour le pic de viewers de la session ouverte (appelé aux connexions chat).

    Le pic concurrent n'augmente qu'aux connexions → pas besoin d'échantillonnage.
    """
    if viewers <= 0:
        return
    session = (
        StreamSession.objects.filter(channel_id=channel_id, ended_at__isnull=True)
        .order_by("-started_at")
        .first()
    )
    if session is not None and viewers > session.peak_viewers:
        session.peak_viewers = viewers
        session.save(update_fields=["peak_viewers"])
        import contextlib

        with contextlib.suppress(Exception):
            from safety.anticheat import evaluate_view_inflation

            evaluate_view_inflation(session.channel, viewers)
