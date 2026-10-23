"""Tests du webhook Bunny Stream : signature, événements live et VOD."""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from django.conf import settings
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel
from channels_app.services import provision_channel

pytestmark = pytest.mark.django_db


def _sign(body: bytes) -> dict[str, str]:
    key = settings.BUNNY_STREAM_WEBHOOK_KEY.encode()
    sig = hmac.new(key, body, hashlib.sha256).hexdigest()
    return {"HTTP_X_BUNNYSTREAM_SIGNATURE": sig}


def _post(client, payload: dict, headers: dict | None = None):
    body = json.dumps(payload).encode()
    return client.post(
        reverse("bunny-stream-webhook"),
        data=body,
        content_type="application/json",
        **(headers if headers is not None else _sign(body)),
    )


def _provisioned(username: str) -> Channel:
    channel = Channel.objects.get(user=UserFactory(username=username))
    provision_channel(channel)
    channel.refresh_from_db()
    return channel


def test_webhook_rejects_missing_signature(client):
    response = _post(client, {"VideoGuid": "x", "Status": 3}, headers={})
    assert response.status_code == 400


def test_webhook_rejects_wrong_signature(client):
    response = _post(
        client,
        {"VideoGuid": "x", "Status": 3},
        headers={"HTTP_X_BUNNYSTREAM_SIGNATURE": "deadbeef"},
    )
    assert response.status_code == 400


def test_webhook_rejects_incomplete_payload(client):
    assert _post(client, {"VideoLibraryId": 1}).status_code == 400


def test_webhook_video_status_is_accepted(client):
    response = _post(client, {"VideoLibraryId": 1, "VideoGuid": "abc", "Status": 3})
    assert response.status_code == 200


def test_webhook_live_online_marks_channel_live(client):
    channel = _provisioned("streamerlive")
    response = _post(client, {"LiveStreamId": channel.stream_id, "State": "Live"})
    assert response.status_code == 200
    channel.refresh_from_db()
    assert channel.is_live


def test_webhook_live_offline_marks_channel_offline(client):
    channel = _provisioned("streamerend")
    channel.is_live = True
    channel.save()
    response = _post(client, {"LiveStreamId": channel.stream_id, "State": "Offline"})
    assert response.status_code == 200
    channel.refresh_from_db()
    assert not channel.is_live


def test_webhook_unknown_stream_is_silent_ok(client):
    response = _post(client, {"LiveStreamId": "ghost", "State": "live"})
    assert response.status_code == 200
