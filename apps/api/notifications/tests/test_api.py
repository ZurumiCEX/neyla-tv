"""Tests notifications : services + endpoints."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel
from notifications import services
from notifications.models import Notification
from social.models import Follow

pytestmark = pytest.mark.django_db


def test_list_requires_auth(api_client):
    assert api_client.get(reverse("notifications-list")).status_code == 401


def test_list_and_unread_count(auth_client_factory):
    user = UserFactory()
    services.create_notification(user, Notification.Type.NEW_FOLLOWER, actor=UserFactory())
    client = auth_client_factory(user)
    data = client.get(reverse("notifications-list")).json()
    assert len(data["results"]) == 1
    assert data["unread"] == 1


def test_mark_read_clears_unread(auth_client_factory):
    user = UserFactory()
    services.create_notification(user, Notification.Type.NEW_FOLLOWER)
    client = auth_client_factory(user)
    client.post(reverse("notifications-read"), {}, format="json")
    assert client.get(reverse("notifications-list")).json()["unread"] == 0


def test_notify_followers_live_creates_one_per_follower():
    streamer = UserFactory(username="strm")
    fan = UserFactory()
    Follow.objects.create(follower=fan, followee=streamer)
    channel = Channel.objects.get(user=streamer)
    created = services.notify_followers_live(channel)
    assert created == 1
    assert Notification.objects.filter(recipient=fan, type=Notification.Type.LIVE_STARTED).exists()


def test_notifications_isolated_per_user(auth_client_factory):
    mine = UserFactory()
    other = UserFactory()
    services.create_notification(other, Notification.Type.NEW_FOLLOWER)
    client = auth_client_factory(mine)
    assert client.get(reverse("notifications-list")).json()["results"] == []


def test_email_live_followers_respects_optin():
    from django.core import mail
    from django.utils import timezone

    from notifications.models import NotificationPreference
    from notifications.tasks import email_live_followers

    streamer = UserFactory(username="emstrm")
    channel = Channel.objects.get(user=streamer)

    verified = UserFactory(email="v@x.com", email_verified_at=timezone.now())
    unverified = UserFactory(email="u@x.com")
    opted_out = UserFactory(email="o@x.com", email_verified_at=timezone.now())
    for fan in (verified, unverified, opted_out):
        Follow.objects.create(follower=fan, followee=streamer)
    NotificationPreference.objects.create(
        user=opted_out, type=Notification.Type.LIVE_STARTED, enabled=False
    )

    mail.outbox.clear()
    sent = email_live_followers(channel.id)
    recipients = {addr for m in mail.outbox for addr in m.to}
    assert sent == 1
    assert recipients == {"v@x.com"}
