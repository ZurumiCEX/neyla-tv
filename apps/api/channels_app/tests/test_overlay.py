"""Tests overlay d'alertes : jeton, test, hook de diffusion."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel

pytestmark = pytest.mark.django_db


def test_my_channel_get_exposes_overlay_token(auth_client_factory):
    user = UserFactory()
    data = auth_client_factory(user).get(reverse("channel-me")).json()
    assert data["overlay_token"]


def test_regenerate_overlay_token_changes_it(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    first = client.get(reverse("channel-me")).json()["overlay_token"]
    regenerated = client.post(reverse("channel-overlay-token")).json()["overlay_token"]
    assert regenerated and regenerated != first
    assert Channel.objects.get(user=user).overlay_token == regenerated


def test_overlay_test_returns_sent(auth_client_factory):
    resp = auth_client_factory(UserFactory()).post(
        reverse("channel-overlay-test"), {"kind": "tip"}, format="json"
    )
    assert resp.status_code == 200
    assert resp.json()["sent"] is True


def test_create_notification_triggers_overlay_alert(monkeypatch):
    from channels_app import alerts
    from notifications import services
    from notifications.models import Notification

    streamer = UserFactory()
    fan = UserFactory()
    calls = []
    monkeypatch.setattr(
        alerts,
        "send_overlay_alert",
        lambda channel_id, kind, actor="", amount=None: calls.append((kind, actor)),
    )
    services.create_notification(
        recipient=streamer,
        type=Notification.Type.NEW_FOLLOWER,
        actor=fan,
        payload={"username": fan.username},
    )
    assert calls and calls[0][0] == "follow"
