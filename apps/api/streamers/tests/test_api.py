"""Tests d'intégration des endpoints candidature streamer."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_apply_requires_auth(api_client):
    assert api_client.post(reverse("streamer-apply")).status_code == 401


def test_apply_requires_rules_acceptance(auth_client_factory):
    client = auth_client_factory(UserFactory())
    response = client.post(reverse("streamer-apply"), {"motivation": "go go"}, format="json")
    assert response.status_code == 400  # rules_accepted manquant


def test_apply_creates_pending_with_score(auth_client_factory):
    client = auth_client_factory(UserFactory())
    payload = {
        "motivation": "Je veux construire une communauté chill autour du retrogaming.",
        "has_streamed": True,
        "community_size": "1k_10k",
        "frequency": "daily",
        "setup": ["pc", "webcam", "microphone"],
        "platforms": {"twitch": "https://twitch.tv/x", "youtube": "https://youtube.com/@x"},
        "content_categories": ["gaming", "irl"],
        "goals": ["community", "revenue"],
        "rules_accepted": True,
    }
    response = client.post(reverse("streamer-apply"), payload, format="json")
    assert response.status_code == 201, response.content
    body = response.json()
    assert body["status"] == "pending"
    assert body["score"] > 50  # signaux forts → score élevé


def test_application_status_none_then_pending(auth_client_factory):
    client = auth_client_factory(UserFactory())
    assert client.get(reverse("streamer-application")).json()["status"] == "none"
    client.post(reverse("streamer-apply"), {"rules_accepted": True}, format="json")
    assert client.get(reverse("streamer-application")).json()["status"] == "pending"
