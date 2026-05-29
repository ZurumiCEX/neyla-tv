"""Tests anti-violation : classification de texte + flags + actions auto."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User
from channels_app.models import Channel
from moderation.models import Report
from safety import scanner, services
from safety.models import ContentFlag

pytestmark = pytest.mark.django_db


def test_classify_text_detects_sexual():
    assert scanner.classify_text("porno gratuit").category == "sexual"


def test_classify_text_detects_gore():
    assert scanner.classify_text("video de torture").category == "gore"


def test_classify_text_safe():
    assert scanner.classify_text("speedrun mario kart").category == "safe"


def test_scan_text_creates_autoblock_and_report():
    user = UserFactory()
    channel = Channel.objects.get(user=user)
    flag = services.scan_text("porno live", "title", channel=channel)
    assert flag is not None
    assert flag.category == ContentFlag.Category.SEXUAL
    assert flag.status == ContentFlag.Status.AUTO_BLOCKED
    # Action auto : un signalement de modération est créé.
    assert Report.objects.filter(channel=channel).exists()


def test_scan_text_safe_no_flag():
    user = UserFactory()
    channel = Channel.objects.get(user=user)
    assert services.scan_text("chill stream", "title", channel=channel) is None


def test_scan_image_no_provider_no_flag():
    user = UserFactory()
    # Sans fournisseur de vision et sans SAFETY_REVIEW_UPLOADS → pas de flag.
    assert services.scan_image("https://cdn/x.jpg", "avatar", user=user) is None


def test_flags_endpoint_requires_moderator(api_client, auth_client_factory):
    assert api_client.get(reverse("safety-flags")).status_code == 401
    assert auth_client_factory(UserFactory()).get(reverse("safety-flags")).status_code == 403


def test_moderator_lists_and_resolves_flag(auth_client_factory):
    owner = UserFactory()
    channel = Channel.objects.get(user=owner)
    flag = services.scan_text("xxx", "title", channel=channel)
    mod = UserFactory(role=User.Role.MODERATOR)
    client = auth_client_factory(mod)
    listed = client.get(reverse("safety-flags")).json()["results"]
    assert any(f["id"] == flag.id for f in listed)
    resp = client.post(
        reverse("safety-flag-resolve", kwargs={"pk": flag.id}), {"action": "reject"}, format="json"
    )
    assert resp.status_code == 200
    flag.refresh_from_db()
    assert flag.status == ContentFlag.Status.REJECTED
