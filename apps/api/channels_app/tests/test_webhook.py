"""Tests du webhook Cloudflare : signature, idempotence, événements."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest
from django.conf import settings
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel
from channels_app.services import provision_channel

pytestmark = pytest.mark.django_db


def _sign(body: bytes, ts: int | None = None) -> dict[str, str]:
    if ts is None:
        ts = int(time.time())
    signed = f"{ts}.".encode() + body
    sig = hmac.new(settings.CLOUDFLARE_WEBHOOK_SECRET.encode(), signed, hashlib.sha256).hexdigest()
    return {"HTTP_WEBHOOK_SIGNATURE": f"time={ts},sig1={sig}"}


def _post(client, payload: dict, headers: dict | None = None):
    body = json.dumps(payload).encode()
    return client.post(
        reverse("cloudflare-stream-webhook"),
        data=body,
        content_type="application/json",
        **(headers or _sign(body)),
    )


def test_webhook_rejects_missing_signature(client):
    response = client.post(
        reverse("cloudflare-stream-webhook"),
        data=b"{}",
        content_type="application/json",
    )
    assert response.status_code == 400


def test_webhook_rejects_wrong_signature(client):
    body = json.dumps({"x": 1}).encode()
    response = client.post(
        reverse("cloudflare-stream-webhook"),
        data=body,
        content_type="application/json",
        HTTP_WEBHOOK_SIGNATURE="time=123,sig1=deadbeef",
    )
    assert response.status_code == 400


def test_webhook_rejects_stale_timestamp(client):
    body = json.dumps({"eventType": "live_input.connected", "data": {"uid": "x"}}).encode()
    response = _post(
        client,
        {"eventType": "live_input.connected", "data": {"uid": "x"}},
        headers=_sign(body, ts=int(time.time()) - 3600),
    )
    assert response.status_code == 400


def test_webhook_connected_marks_channel_live(client):
    user = UserFactory(username="streamerlive")
    channel = Channel.objects.get(user=user)
    provision_channel(channel)
    channel.refresh_from_db()
    response = _post(
        client,
        {
            "eventType": "live_input.connected",
            "data": {"live_input_uid": channel.live_input_uid},
        },
    )
    assert response.status_code == 200
    channel.refresh_from_db()
    assert channel.is_live


def test_webhook_disconnected_marks_channel_offline(client):
    user = UserFactory(username="streamerend")
    channel = Channel.objects.get(user=user)
    provision_channel(channel)
    channel.is_live = True
    channel.save()
    response = _post(
        client,
        {
            "eventType": "live_input.disconnected",
            "data": {"live_input_uid": channel.live_input_uid},
        },
    )
    assert response.status_code == 200
    channel.refresh_from_db()
    assert not channel.is_live


def test_webhook_unknown_uid_is_silent_ok(client):
    response = _post(
        client,
        {"eventType": "live_input.connected", "data": {"live_input_uid": "ghost"}},
    )
    assert response.status_code == 200
