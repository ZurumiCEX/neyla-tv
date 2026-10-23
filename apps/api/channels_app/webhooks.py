"""Webhook Bunny Stream : signature HMAC-SHA256, idempotent.

Bunny envoie un POST JSON à chaque changement d'état d'une vidéo :

    {"VideoLibraryId": 123, "VideoGuid": "…", "Status": 3}

signé via l'en-tête `X-BunnyStream-Signature` = hex(hmac_sha256(clé, corps brut)),
la clé étant `BUNNY_STREAM_WEBHOOK_KEY`.

- Statuts VOD (« Instant ») : 3 = encodage terminé, 4 = résolution prête,
  5 = échec → délégués à `shorts.services.handle_video_status`.
- Événements live (best-effort, non documentés par Bunny) : si la charge contient
  un identifiant de live stream et un état, la chaîne est basculée live/offline.
  La source de vérité live reste le polling `channels_app.tasks.sync_live_status`.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Channel
from .services import mark_live, mark_offline

logger = logging.getLogger(__name__)

SIGNATURE_HEADER = "HTTP_X_BUNNYSTREAM_SIGNATURE"
LIVE_ONLINE = {"live", "online", "started", "connected", "streaming"}
LIVE_OFFLINE = {"offline", "ended", "stopped", "disconnected", "idle"}


def verify_signature(raw_body: bytes, provided: str) -> bool:
    """Compare en temps constant (hex ou base64 acceptés)."""
    if not provided:
        return False
    key = (settings.BUNNY_STREAM_WEBHOOK_KEY or "").encode()
    digest = hmac.new(key, raw_body, hashlib.sha256).digest()
    candidates = (digest.hex(), base64.b64encode(digest).decode())
    provided = provided.strip()
    return any(hmac.compare_digest(c, provided) for c in candidates)


def _handle_live_event(stream_id: str, state: str) -> None:
    channel = Channel.objects.filter(stream_id=stream_id).first()
    if channel is None:
        logger.warning("webhook bunny: live stream %s sans chaîne associée", stream_id)
        return
    if state in LIVE_ONLINE:
        if mark_live(channel):
            from notifications.services import notify_followers_live

            notify_followers_live(channel)
    elif state in LIVE_OFFLINE:
        mark_offline(channel)
    else:
        logger.info("webhook bunny: état live non géré %s", state)


def _handle_video_event(video_guid: str, status: int) -> None:
    try:
        from shorts.services import handle_video_status
    except ImportError:  # app « Instant » absente
        return
    handle_video_status(video_guid, status)


@csrf_exempt
@require_POST
def bunny_stream_webhook(request: HttpRequest) -> HttpResponse:
    if not verify_signature(request.body, request.META.get(SIGNATURE_HEADER, "")):
        logger.warning("webhook bunny: signature invalide ou manquante")
        return JsonResponse({"detail": "Signature invalide."}, status=400)
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON invalide."}, status=400)
    if not isinstance(payload, dict):
        return JsonResponse({"detail": "Payload invalide."}, status=400)

    stream_id = str(payload.get("LiveStreamId") or payload.get("StreamId") or "")
    if stream_id:
        state = str(payload.get("State") or payload.get("Status") or "").lower()
        _handle_live_event(stream_id, state)
        return JsonResponse({"detail": "ok"})

    video_guid = str(payload.get("VideoGuid") or "")
    status = payload.get("Status")
    if not video_guid or status is None:
        return JsonResponse({"detail": "Payload incomplet."}, status=400)
    try:
        status_code = int(status)
    except (TypeError, ValueError):
        return JsonResponse({"detail": "Statut invalide."}, status=400)
    _handle_video_event(video_guid, status_code)
    return JsonResponse({"detail": "ok"})
