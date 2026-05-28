"""Tests API de gestion des bans chat (streamer)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel
from chat.models import ChatBan, ChatIpBan

pytestmark = pytest.mark.django_db


def test_my_chat_bans_requires_auth(api_client):
    assert api_client.get(reverse("chat-my-bans")).status_code == 401


def test_lists_active_user_and_ip_bans(auth_client_factory):
    streamer = UserFactory()
    channel = Channel.objects.get(user=streamer)
    target = UserFactory(username="troll")
    ChatBan.objects.create(channel=channel, user=target, until=None, shadow=True)
    ChatIpBan.objects.create(channel=channel, ip="1.2.3.4", until=None)

    data = auth_client_factory(streamer).get(reverse("chat-my-bans")).json()
    assert [b["username"] for b in data["user_bans"]] == ["troll"]
    assert data["user_bans"][0]["shadow"] is True
    assert [b["ip"] for b in data["ip_bans"]] == ["1.2.3.4"]


def test_lift_user_ban(auth_client_factory):
    streamer = UserFactory()
    channel = Channel.objects.get(user=streamer)
    target = UserFactory(username="troll2")
    ChatBan.objects.create(channel=channel, user=target, until=None)

    resp = auth_client_factory(streamer).delete(
        reverse("chat-lift-user-ban", kwargs={"username": "troll2"})
    )
    assert resp.status_code == 204
    assert not ChatBan.objects.filter(channel=channel, user=target).exists()


def test_lift_ip_ban(auth_client_factory):
    streamer = UserFactory()
    channel = Channel.objects.get(user=streamer)
    ChatIpBan.objects.create(channel=channel, ip="9.8.7.6", until=None)

    resp = auth_client_factory(streamer).delete(
        reverse("chat-lift-ip-ban", kwargs={"ip": "9.8.7.6"})
    )
    assert resp.status_code == 204
    assert not ChatIpBan.objects.filter(channel=channel, ip="9.8.7.6").exists()


def test_cannot_see_other_channel_bans(auth_client_factory):
    streamer = UserFactory()
    other = UserFactory()
    other_channel = Channel.objects.get(user=other)
    ChatBan.objects.create(channel=other_channel, user=UserFactory(), until=None)

    data = auth_client_factory(streamer).get(reverse("chat-my-bans")).json()
    assert data["user_bans"] == []
