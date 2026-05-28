"""Tests Web Push : abonnement, clé publique, envoi aux followers."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel
from notifications import push as push_module
from notifications import tasks
from notifications.models import PushSubscription
from social.models import Follow

pytestmark = pytest.mark.django_db


def _auth(user):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def test_subscribe_then_unsubscribe():
    user = UserFactory()
    client = _auth(user)
    body = {"endpoint": "https://push.example/abc", "keys": {"p256dh": "p", "auth": "a"}}
    resp = client.post(reverse("notifications-push-subscribe"), body, format="json")
    assert resp.status_code == 201
    assert PushSubscription.objects.filter(user=user, endpoint=body["endpoint"]).exists()

    resp = client.post(
        reverse("notifications-push-unsubscribe"),
        {"endpoint": body["endpoint"]},
        format="json",
    )
    assert resp.status_code == 204
    assert not PushSubscription.objects.filter(endpoint=body["endpoint"]).exists()


def test_subscribe_rejects_incomplete():
    client = _auth(UserFactory())
    resp = client.post(
        reverse("notifications-push-subscribe"),
        {"endpoint": "https://push.example/x"},
        format="json",
    )
    assert resp.status_code == 400


def test_push_key_endpoint():
    resp = _auth(UserFactory()).get(reverse("notifications-push-key"))
    assert resp.status_code == 200
    assert "public_key" in resp.json()


def test_push_live_followers_skips_when_unconfigured():
    # VAPID non configuré par défaut → 0 envoi.
    streamer = UserFactory()
    channel = Channel.objects.get(user=streamer)
    fan = UserFactory()
    Follow.objects.create(follower=fan, followee=streamer)
    PushSubscription.objects.create(user=fan, endpoint="https://p/x", p256dh="p", auth="a")
    assert tasks.push_live_followers(channel.id) == 0


def test_push_live_followers_sends_when_configured(monkeypatch):
    streamer = UserFactory()
    channel = Channel.objects.get(user=streamer)
    fan = UserFactory()
    Follow.objects.create(follower=fan, followee=streamer)
    PushSubscription.objects.create(user=fan, endpoint="https://p/x", p256dh="p", auth="a")

    monkeypatch.setattr(push_module, "is_configured", lambda: True)
    sent_payloads = []
    monkeypatch.setattr(
        push_module,
        "send_to_subscription",
        lambda sub, payload: sent_payloads.append(payload) or True,
    )
    assert tasks.push_live_followers(channel.id) == 1
    assert sent_payloads and "title" in sent_payloads[0]
