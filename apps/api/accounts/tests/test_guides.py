"""Tests suivi des acquis (tutoriels)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import GuideProgress

pytestmark = pytest.mark.django_db


def test_progress_requires_auth(api_client):
    assert api_client.get(reverse("guides-progress")).status_code == 401


def test_mark_and_unmark_step(auth_client_factory):
    client = auth_client_factory(UserFactory())
    url = reverse("guides-progress")
    assert client.get(url).json()["completed"] == []

    done = client.post(url, {"key": "streaming-setup:1"}, format="json").json()
    assert done["completed"] == ["streaming-setup:1"]

    undone = client.post(url, {"key": "streaming-setup:1", "done": False}, format="json").json()
    assert undone["completed"] == []


def test_progress_isolated_per_user(auth_client_factory):
    a, b = UserFactory(), UserFactory()
    GuideProgress.objects.create(user=a, key="x:1")
    assert auth_client_factory(b).get(reverse("guides-progress")).json()["completed"] == []


def test_mark_is_idempotent(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    url = reverse("guides-progress")
    client.post(url, {"key": "k:1"}, format="json")
    client.post(url, {"key": "k:1"}, format="json")
    assert GuideProgress.objects.filter(user=user, key="k:1").count() == 1
