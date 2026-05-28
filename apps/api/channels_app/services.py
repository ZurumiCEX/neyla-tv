"""Services métier des chaînes (provisionnement, rotation, live on/off)."""

from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from .cloudflare import CloudflareStreamError, get_client
from .models import Channel, StreamSession

logger = logging.getLogger(__name__)


@transaction.atomic
def provision_channel(channel: Channel) -> Channel:
    """Crée le Live Input Cloudflare et stocke les credentials. Idempotent."""
    if channel.is_provisioned:
        return channel
    client = get_client()
    live = client.create_live_input(label=f"channel:{channel.slug}")
    channel.live_input_uid = live.uid
    channel.rtmps_url = live.rtmps_url
    channel.rtmps_key = live.rtmps_key
    channel.hls_playback_url = live.hls_playback_url
    channel.save(
        update_fields=[
            "live_input_uid",
            "rtmps_url",
            "rtmps_key",
            "hls_playback_url",
            "updated_at",
        ]
    )
    return channel


@transaction.atomic
def rotate_stream_key(channel: Channel) -> Channel:
    """Supprime l'ancien Live Input et en crée un nouveau. Force OBS à reconfigurer."""
    client = get_client()
    old_uid = channel.live_input_uid
    if old_uid:
        try:
            client.delete_live_input(old_uid)
        except CloudflareStreamError:
            logger.exception("rotate_stream_key: delete ancien live_input failed")
    channel.live_input_uid = ""
    channel.rtmps_url = ""
    channel.rtmps_key = ""
    channel.hls_playback_url = ""
    channel.is_live = False
    channel.save(
        update_fields=[
            "live_input_uid",
            "rtmps_url",
            "rtmps_key",
            "hls_playback_url",
            "is_live",
            "updated_at",
        ]
    )
    return provision_channel(channel)


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
