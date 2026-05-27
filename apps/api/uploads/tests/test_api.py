"""Tests upload (mode FAKE) : avatar, bannière, vignette de jeu, validation."""

from __future__ import annotations

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User
from catalog.models import Game
from channels_app.models import Channel

pytestmark = pytest.mark.django_db


def _png(name="a.png", content_type="image/png"):
    return SimpleUploadedFile(name, b"\x89PNG\r\n\x1a\n fake", content_type=content_type)


def test_avatar_upload_sets_url(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    resp = client.post(reverse("upload-avatar"), {"file": _png()}, format="multipart")
    assert resp.status_code == 201
    url = resp.json()["url"]
    user.refresh_from_db()
    assert user.avatar_url == url
    assert url.endswith(".png")


def test_banner_upload_sets_channel_url(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    resp = client.post(reverse("upload-banner"), {"file": _png()}, format="multipart")
    assert resp.status_code == 201
    assert Channel.objects.get(user=user).banner_url == resp.json()["url"]


def test_rejects_unsupported_type(auth_client_factory):
    client = auth_client_factory(UserFactory())
    bad = SimpleUploadedFile("a.gif", b"GIF89a", content_type="image/gif")
    resp = client.post(reverse("upload-avatar"), {"file": bad}, format="multipart")
    assert resp.status_code == 400


def test_game_upload_requires_admin(auth_client_factory):
    Game.objects.create(slug="lol", name="LoL")
    resp = auth_client_factory(UserFactory()).post(
        reverse("upload-game", kwargs={"slug": "lol"}), {"file": _png()}, format="multipart"
    )
    assert resp.status_code == 403


def test_game_upload_as_admin(auth_client_factory):
    Game.objects.create(slug="cs2", name="CS2")
    admin = UserFactory(role=User.Role.ADMIN)
    resp = auth_client_factory(admin).post(
        reverse("upload-game", kwargs={"slug": "cs2"}), {"file": _png()}, format="multipart"
    )
    assert resp.status_code == 201
    assert Game.objects.get(slug="cs2").box_art_url == resp.json()["url"]
