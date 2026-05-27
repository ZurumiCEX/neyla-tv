"""Tests d'intégration des endpoints REST des chaînes."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel
from channels_app.services import provision_channel

pytestmark = pytest.mark.django_db


def test_my_channel_requires_auth(api_client):
    response = api_client.get(reverse("channel-me"))
    assert response.status_code == 401


def test_my_channel_unprovisioned_has_no_credentials(auth_client_factory):
    """Sans approbation streamer : chaîne non provisionnée, pas de clé RTMPS."""
    user = UserFactory()
    client = auth_client_factory(user)
    response = client.get(reverse("channel-me"))
    assert response.status_code == 200
    data = response.json()
    assert data["is_provisioned"] is False
    assert data["rtmps_url"] == ""
    assert data["rtmps_key"] == ""


def test_my_channel_provisioned_returns_credentials(auth_client_factory):
    user = UserFactory()
    provision_channel(Channel.objects.get(user=user))
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


def test_rotate_key_forbidden_when_unprovisioned(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    response = client.post(reverse("channel-rotate-key"))
    assert response.status_code == 403


def test_rotate_key_changes_rtmps_key_when_provisioned(auth_client_factory):
    user = UserFactory()
    provision_channel(Channel.objects.get(user=user))
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


def test_channel_status_returns_minimal_payload(api_client):
    user = UserFactory(username="status1")
    Channel.objects.filter(user=user).update(is_live=True)
    response = api_client.get(reverse("channel-status", kwargs={"slug": "status1"}))
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"is_live", "last_live_started_at", "viewers"}
    assert data["is_live"] is True
    assert response.headers.get("Cache-Control") == "public, max-age=5"


def test_channel_status_404_when_unknown(api_client):
    response = api_client.get(reverse("channel-status", kwargs={"slug": "ghost"}))
    assert response.status_code == 404


def test_my_channel_get_includes_follower_count_and_viewers(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    data = client.get(reverse("channel-me")).json()
    assert data["follower_count"] == 0
    assert data["viewers"] == 0


def test_my_sessions_lists_owner_sessions(auth_client_factory):
    from channels_app.services import mark_live

    user = UserFactory()
    mark_live(Channel.objects.get(user=user))
    client = auth_client_factory(user)
    response = client.get(reverse("channel-sessions"))
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["ended_at"] is None
