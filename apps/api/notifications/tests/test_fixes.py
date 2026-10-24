"""Corrections du module notifications : préférences, abonnements offerts, tips, pagination."""

from __future__ import annotations

from unittest import mock

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.testing import provisioned_channel
from notifications import services
from notifications.models import Notification, NotificationPreference
from payments import services as pay
from social.models import Follow
from subscriptions import services as subs

pytestmark = pytest.mark.django_db


def test_live_notification_respects_disabled_preference():
    channel = provisioned_channel(UserFactory())
    keen, muted = UserFactory(), UserFactory()
    Follow.objects.create(follower=keen, followee=channel.user)
    Follow.objects.create(follower=muted, followee=channel.user)
    NotificationPreference.objects.create(
        user=muted, type=Notification.Type.LIVE_STARTED, enabled=False
    )
    assert services.notify_followers_live(channel) == 1
    assert Notification.objects.filter(recipient=keen).count() == 1
    assert not Notification.objects.filter(recipient=muted).exists()


def test_gift_alerts_streamer_channel_and_notifies_recipient(django_capture_on_commit_callbacks):
    channel = provisioned_channel(UserFactory())
    subs.set_tier(channel, price_aura=100, perks=[])
    gifter, recipient = UserFactory(), UserFactory()
    provisioned_channel(recipient)  # le destinataire a sa propre chaîne
    pay.create_purchase(gifter, 500)

    with (
        mock.patch("channels_app.alerts.send_overlay_alert") as alert,
        django_capture_on_commit_callbacks(execute=True),
    ):
        subs.gift_subscription(gifter, channel.slug, recipient.username)

    # Une seule alerte overlay, sur la chaîne du streamer, de type « gift ».
    assert alert.call_count == 1
    channel_id, kind = alert.call_args.args[:2]
    assert channel_id == channel.id
    assert kind == "gift"
    assert recipient.username in alert.call_args.kwargs["actor"]

    to_streamer = Notification.objects.get(recipient=channel.user)
    assert to_streamer.type == Notification.Type.SUBSCRIPTION
    assert to_streamer.payload["gifted"] is True
    to_recipient = Notification.objects.get(recipient=recipient)
    assert to_recipient.type == Notification.Type.SUBSCRIPTION_GIFT
    assert to_recipient.payload == {"gifter": gifter.username, "channel": channel.slug}


def test_tip_notification_carries_amount_sent(django_capture_on_commit_callbacks):
    channel = provisioned_channel(UserFactory())
    fan = UserFactory()
    pay.create_purchase(fan, 500)
    with django_capture_on_commit_callbacks(execute=True):
        pay.send_tip(fan, channel.slug, 100, "GG")
    notif = Notification.objects.get(recipient=channel.user, type=Notification.Type.TIP_RECEIVED)
    assert notif.payload["aura"] == 100
    assert notif.payload["creator_share"] < 100


def test_list_is_paginated_by_cursor(auth_client_factory):
    user = UserFactory()
    for i in range(35):
        Notification.objects.create(
            recipient=user, type=Notification.Type.NEW_FOLLOWER, payload={"n": i}
        )
    client = auth_client_factory(user)
    first = client.get(reverse("notifications-list")).json()
    assert len(first["results"]) == 30
    assert first["unread"] == 35
    assert first["next_before"] is not None
    second = client.get(reverse("notifications-list"), {"before": first["next_before"]}).json()
    assert len(second["results"]) == 5
    assert second["next_before"] is None
    ids = [n["id"] for n in first["results"] + second["results"]]
    assert len(set(ids)) == 35


def test_mark_all_read_can_keep_support_messages(auth_client_factory):
    user = UserFactory()
    for _ in range(40):
        Notification.objects.create(recipient=user, type=Notification.Type.NEW_FOLLOWER)
    Notification.objects.create(
        recipient=user, type=Notification.Type.SUPPORT_MESSAGE, payload={"title": "x"}
    )
    resp = auth_client_factory(user).post(
        reverse("notifications-read"), {"except": ["support_message"]}, format="json"
    )
    assert resp.json() == {"marked": 40, "unread": 1}
