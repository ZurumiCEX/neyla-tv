"""Webhook Cloudflare Stream : signature HMAC-SHA256, anti-rejeu, idempotent.

Format de l'entête (aligné sur le style Cloudflare Worker / R2) :
    Webhook-Signature: time=<unix_seconds>,sig1=<hex_sha256>

Avec :
    sig1 = hex(hmac_sha256(secret, f"{time}.{raw_body}"))
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Channel
from .services import mark_live, mark_offline

logger = logging.getLogger(__name__)

SIGNATURE_HEADER = "HTTP_WEBHOOK_SIGNATURE"


def _parse_signature_header(raw: str) -> tuple[int, str] | None:
    parts: dict[str, str] = {}
    for chunk in raw.split(","):
        if "=" in chunk:
            k, v = chunk.strip().split("=", 1)
            parts[k] = v
    try:
        return int(parts["time"]), parts["sig1"]
    except (KeyError, ValueError):
        return None


def _verify_signature(raw_body: bytes, header_value: str) -> bool:
    parsed = _parse_signature_header(header_value)
    if parsed is None:
        return False
    timestamp, provided = parsed
    drift = abs(time.time() - timestamp)
    if drift > settings.WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS:
        return False
    signed = f"{timestamp}.".encode() + raw_body
    expected = hmac.new(
        settings.CLOUDFLARE_WEBHOOK_SECRET.encode(), signed, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, provided)


def _handle_event(event_type: str, live_input_uid: str) -> None:
    channel = Channel.objects.filter(live_input_uid=live_input_uid).first()
    if channel is None:
        logger.warning("webhook: live_input %s sans chaîne associée", live_input_uid)
        return
    if event_type == "live_input.connected":
        if mark_live(channel):
            from notifications.services import notify_followers_live

            notify_followers_live(channel)
    elif event_type == "live_input.disconnected":
        mark_offline(channel)
    else:
        logger.info("webhook: événement non géré %s", event_type)


@csrf_exempt
@require_POST
def cloudflare_stream_webhook(request: HttpRequest) -> HttpResponse:
    header_value = request.META.get(SIGNATURE_HEADER, "")
    if not header_value or not _verify_signature(request.body, header_value):
        logger.warning("webhook: signature invalide ou manquante")
        return JsonResponse({"detail": "Signature invalide."}, status=400)
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "JSON invalide."}, status=400)
    event_type = payload.get("eventType") or payload.get("type") or ""
    data = payload.get("data") or payload
    live_input_uid = data.get("live_input_uid") or data.get("uid") or ""
    if not event_type or not live_input_uid:
        return JsonResponse({"detail": "Payload incomplet."}, status=400)
    _handle_event(event_type, live_input_uid)
    return JsonResponse({"detail": "ok"})
