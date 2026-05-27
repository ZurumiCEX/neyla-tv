"""Tests d'intégration des endpoints candidature streamer."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_apply_requires_auth(api_client):
    assert api_client.post(reverse("streamer-apply")).status_code == 401


def test_apply_creates_pending(auth_client_factory):
    client = auth_client_factory(UserFactory())
    response = client.post(reverse("streamer-apply"), {"motivation": "go go"}, format="json")
    assert response.status_code == 201
    assert response.json()["status"] == "pending"


def test_application_status_none_then_pending(auth_client_factory):
    client = auth_client_factory(UserFactory())
    assert client.get(reverse("streamer-application")).json()["status"] == "none"
    client.post(reverse("streamer-apply"), {"motivation": ""}, format="json")
    assert client.get(reverse("streamer-application")).json()["status"] == "pending"
