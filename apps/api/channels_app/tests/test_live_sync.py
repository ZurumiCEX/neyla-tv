"""Synchronisation live/offline par polling Bunny + bascule manuelle gardée."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.bunny import FakeBunnyStreamClient, LiveStatus
from channels_app.models import Channel, StreamSession
from channels_app.services import provision_channel
from channels_app.tasks import sync_channel_status, sync_live_status

pytestmark = pytest.mark.django_db


class _StubClient(FakeBunnyStreamClient):
    is_fake = False

    def __init__(self, live: bool):
        self._live = live

    def get_live_status(self, stream_id: str) -> LiveStatus:  # noqa: ARG002
        return LiveStatus(is_live=self._live)


def _provisioned() -> Channel:
    channel = Channel.objects.get(user=UserFactory())
    provision_channel(channel)
    channel.refresh_from_db()
    return channel


def test_sync_marks_live_then_offline_and_closes_session():
    channel = _provisioned()
    assert sync_channel_status(channel, _StubClient(True)) is True
    channel.refresh_from_db()
    assert channel.is_live
    assert channel.stream_checked_at is not None
    assert StreamSession.objects.filter(channel=channel, ended_at__isnull=True).count() == 1

    assert sync_channel_status(channel, _StubClient(False)) is False
    channel.refresh_from_db()
    assert not channel.is_live
    assert StreamSession.objects.filter(channel=channel, ended_at__isnull=True).count() == 0


def test_sync_skips_in_fake_mode():
    channel = _provisioned()
    assert sync_channel_status(channel, FakeBunnyStreamClient()) is None
    assert sync_live_status() == 0  # pas de clé API en tests → FAKE


def test_manual_go_live_forbidden_when_unprovisioned(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    response = client.post(reverse("channel-set-live"), {"live": True}, format="json")
    assert response.status_code == 403
    assert not Channel.objects.get(user=user).is_live


def test_manual_go_live_allowed_when_provisioned(auth_client_factory):
    user = UserFactory()
    provision_channel(Channel.objects.get(user=user))
    client = auth_client_factory(user)
    response = client.post(reverse("channel-set-live"), {"live": True}, format="json")
    assert response.status_code == 200
    assert response.json()["is_live"] is True


def test_stream_health_requires_provisioning(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    assert client.get(reverse("channel-stream-health")).status_code == 403
    provision_channel(Channel.objects.get(user=user))
    data = client.get(reverse("channel-stream-health")).json()
    assert data["provider"] == "bunny"
    assert data["mode"] == "fake"


def test_overlay_info_exposes_goal_progress(auth_client_factory, api_client):
    from payments import services as pay

    streamer = UserFactory()
    channel = Channel.objects.get(user=streamer)
    provision_channel(channel)
    client = auth_client_factory(streamer)
    data = client.get(reverse("channel-me")).json()
    token = data["overlay_token"]
    patched = client.patch(
        reverse("channel-me"),
        {"goal_title": "Nouvelle webcam", "goal_kind": "tips", "goal_target": 500},
        format="json",
    )
    assert patched.status_code == 200
    assert patched.json()["goal_started_at"] is not None

    fan = UserFactory()
    pay.create_purchase(fan, 200)
    pay.send_tip(fan, channel.slug, 120)
    info = api_client.get(reverse("overlay-info", kwargs={"token": token})).json()
    assert info["slug"] == channel.slug
    assert info["goal"] == {
        "title": "Nouvelle webcam",
        "kind": "tips",
        "target": 500,
        "current": 120,
    }


def test_overlay_info_unknown_token_404(api_client):
    assert api_client.get(reverse("overlay-info", kwargs={"token": "nope"})).status_code == 404
