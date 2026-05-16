"""Tests d'intégration des endpoints REST des chaînes."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel

pytestmark = pytest.mark.django_db


def test_my_channel_requires_auth(api_client):
    response = api_client.get(reverse("channel-me"))
    assert response.status_code == 401


def test_my_channel_returns_rtmps_credentials(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    response = client.get(reverse("channel-me"))
    assert response.status_code == 200
    data = response.json()
    assert data["rtmps_url"] == "rtmps://fake.local/live"
    assert data["rtmps_key"].startswith("fake-key-")
    assert data["is_provisioned"]


def test_patch_my_channel_updates_title(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    response = client.patch(
        reverse("channel-me"),
        {"title": "Speedrun Mario 64", "thumbnail_url": "https://img.example/x.jpg"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Speedrun Mario 64"


def test_rotate_key_changes_rtmps_key(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    before = client.get(reverse("channel-me")).json()
    rotated = client.post(reverse("channel-rotate-key")).json()
    assert rotated["rtmps_key"] != before["rtmps_key"]


def test_public_channel_excludes_rtmps_credentials(api_client):
    user = UserFactory(username="public1")
    Channel.objects.filter(user=user).update(title="Bonjour")
    response = api_client.get(reverse("channel-public", kwargs={"slug": "public1"}))
    assert response.status_code == 200
    data = response.json()
    assert "rtmps_url" not in data
    assert "rtmps_key" not in data
    assert data["streamer"]["username"] == "public1"


def test_public_channel_404_when_unknown(api_client):
    response = api_client.get(reverse("channel-public", kwargs={"slug": "ghost"}))
    assert response.status_code == 404
