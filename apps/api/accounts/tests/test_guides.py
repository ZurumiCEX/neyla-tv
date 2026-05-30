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


# --- Guides gérés en base (contenu) -----------------------------------------


def test_guides_seeded_by_migration():
    from accounts.models import Guide, GuideStep

    assert Guide.objects.count() == 5
    assert GuideStep.objects.filter(guide__slug="streaming-setup").count() == 5


def test_guides_list_public_and_localized(api_client):
    resp = api_client.get(reverse("guides-list"), {"locale": "en"})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 5
    gs = next(g for g in results if g["slug"] == "getting-started")
    assert gs["title"] == "Getting started"
    assert gs["steps"][0]["id"] == "verify-email"


def test_guides_list_unpublished_hidden(api_client):
    from accounts.models import Guide

    Guide.objects.filter(slug="security").update(is_published=False)
    slugs = [g["slug"] for g in api_client.get(reverse("guides-list")).json()["results"]]
    assert "security" not in slugs


def test_guides_admin_changelist_lists_guides(client):
    from accounts.models import User

    boss = User.objects.create_superuser(
        username="boss-guide", email="boss-guide@example.com", password="pw-12345"
    )
    client.force_login(boss)
    resp = client.get("/admin/accounts/guide/")
    assert resp.status_code == 200
    assert b"getting-started" in resp.content
