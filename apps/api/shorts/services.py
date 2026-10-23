"""Logique « Instant » : upload Bunny, fil tendance, vues et likes."""

from __future__ import annotations

import contextlib
import logging

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from channels_app.bunny import (
    FAKE_SHORT_URL,
    BunnyStreamError,
    get_client,
    video_playback_url,
    video_thumbnail_url,
)
from channels_app.models import Channel

from .models import Short, ShortLike

logger = logging.getLogger(__name__)

MAX_DURATION_S = 60
MAX_PENDING_UPLOADS = 5
TRENDING_POOL = 500
VIEW_DEDUP_SECONDS = 6 * 3600

# Statuts d'encodage Bunny (webhook) : 3 = terminé, 4 = résolution prête, 5/6 = échec.
BUNNY_READY = {3, 4}
BUNNY_FAILED = {5, 6}


class ShortError(Exception):
    """Erreur métier « Instant »."""


def _streamer_channel(user) -> Channel:
    channel = Channel.objects.filter(user=user).first()
    if channel is None or not channel.is_provisioned:
        raise ShortError("Seuls les streamers approuvés peuvent publier des vidéos Instant.")
    return channel


def create_upload(user, title: str) -> tuple[Short, dict]:
    """Crée la vidéo côté Bunny et renvoie les paramètres d'upload TUS signés.

    En mode FAKE (pas de clé Bunny), la vidéo est publiée immédiatement avec un
    clip de démonstration : l'interface reste testable de bout en bout.
    """
    title = (title or "").strip()[:120]
    if not title:
        raise ShortError("Donne un titre à ta vidéo.")
    channel = _streamer_channel(user)
    pending = Short.objects.filter(
        channel=channel, status__in=[Short.Status.UPLOADING, Short.Status.PROCESSING]
    ).count()
    if pending >= MAX_PENDING_UPLOADS:
        raise ShortError("Trop de vidéos en cours de traitement : patiente un peu.")

    client = get_client()
    try:
        guid = client.create_video(title)
    except BunnyStreamError as exc:
        logger.exception("shorts: création vidéo Bunny échouée")
        raise ShortError("Le service vidéo est indisponible, réessaie plus tard.") from exc

    short = Short.objects.create(channel=channel, title=title, video_guid=guid)
    if client.is_fake:
        _mark_ready(short, playback=FAKE_SHORT_URL, thumbnail=channel.thumbnail_url)
        return short, {"mode": "fake"}

    upload = client.upload_params(guid)
    return short, {
        "mode": "tus",
        "endpoint": upload.endpoint,
        "library_id": upload.library_id,
        "video_id": upload.video_id,
        "expires": upload.expires,
        "signature": upload.signature,
        "max_duration_s": MAX_DURATION_S,
    }


def mark_uploaded(user, short_id: int) -> Short:
    """Le navigateur a terminé l'envoi : la vidéo part en encodage."""
    short = Short.objects.filter(pk=short_id, channel__user=user).first()
    if short is None:
        raise ShortError("Vidéo introuvable.")
    if short.status == Short.Status.UPLOADING:
        short.status = Short.Status.PROCESSING
        short.save(update_fields=["status"])
    return short


def _mark_ready(short: Short, playback: str, thumbnail: str = "", duration: int = 0) -> None:
    short.status = Short.Status.READY
    short.playback_url = playback
    short.thumbnail_url = thumbnail or short.thumbnail_url
    short.duration_s = duration or short.duration_s
    short.published_at = short.published_at or timezone.now()
    short.save(
        update_fields=["status", "playback_url", "thumbnail_url", "duration_s", "published_at"]
    )


def handle_video_status(video_guid: str, status: int) -> None:
    """Appelé par le webhook Bunny à chaque changement d'état d'encodage."""
    short = Short.objects.filter(video_guid=video_guid).first()
    if short is None:
        return
    if status in BUNNY_FAILED:
        Short.objects.filter(pk=short.pk).update(status=Short.Status.FAILED)
        return
    if status not in BUNNY_READY or short.status == Short.Status.READY:
        return
    duration = 0
    with contextlib.suppress(Exception):
        duration = int(float(get_client().get_video(video_guid).get("length") or 0))
    if duration > MAX_DURATION_S:
        Short.objects.filter(pk=short.pk).update(status=Short.Status.FAILED, duration_s=duration)
        with contextlib.suppress(BunnyStreamError):
            get_client().delete_video(video_guid)
        return
    _mark_ready(
        short,
        playback=video_playback_url(video_guid),
        thumbnail=video_thumbnail_url(video_guid),
        duration=duration,
    )


def delete_short(user, short_id: int) -> None:
    short = Short.objects.filter(pk=short_id, channel__user=user).first()
    if short is None:
        raise ShortError("Vidéo introuvable.")
    with contextlib.suppress(BunnyStreamError):
        get_client().delete_video(short.video_guid)
    short.delete()


def visible_shorts():
    return Short.objects.filter(
        status=Short.Status.READY, is_published=True, channel__stream_id__gt=""
    ).select_related("channel__user")


def trending_score(short: Short, now=None) -> float:
    """Popularité amortie par l'âge (façon « hot ») : les créateurs que tu ne
    suis pas remontent aussi, et le fil se renouvelle."""
    now = now or timezone.now()
    age_h = max(0.0, (now - (short.published_at or short.created_at)).total_seconds() / 3600)
    return (short.view_count + 5 * short.like_count + 1) / ((age_h + 2) ** 1.5)


def trending(limit: int = 20, offset: int = 0) -> list[Short]:
    pool = list(visible_shorts().order_by("-published_at")[:TRENDING_POOL])
    now = timezone.now()
    pool.sort(key=lambda s: trending_score(s, now), reverse=True)
    return pool[offset : offset + limit]


def register_view(short: Short, viewer_key: str) -> bool:
    """+1 vue, au plus une fois par spectateur et par fenêtre de 6 h."""
    if not short.is_visible:
        return False
    try:
        import redis

        client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        # La date de création rend la clé unique même si un id est réutilisé.
        key = f"short:view:{short.pk}:{int(short.created_at.timestamp())}:{viewer_key}"
        fresh = client.set(key, "1", nx=True, ex=VIEW_DEDUP_SECONDS)
    except Exception:  # noqa: BLE001 — Redis indisponible : on compte quand même
        fresh = True
    if not fresh:
        return False
    Short.objects.filter(pk=short.pk).update(view_count=F("view_count") + 1)
    return True


def like(user, short: Short) -> bool:
    if not short.is_visible:
        raise ShortError("Vidéo indisponible.")
    try:
        with transaction.atomic():
            ShortLike.objects.create(user=user, short=short)
    except IntegrityError:
        return False
    Short.objects.filter(pk=short.pk).update(like_count=F("like_count") + 1)
    return True


def unlike(user, short: Short) -> bool:
    deleted, _ = ShortLike.objects.filter(user=user, short=short).delete()
    if deleted:
        Short.objects.filter(pk=short.pk, like_count__gt=0).update(like_count=F("like_count") - 1)
    return bool(deleted)
