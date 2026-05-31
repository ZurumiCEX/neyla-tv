"""Tests annonces : fenêtre temporelle + ciblage d'audience."""

from __future__ import annotations

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.factories import UserFactory
from announcements.models import SiteAnnouncement

pytestmark = pytest.mark.django_db


def _mk(**overrides):
    now = timezone.now()
    defaults = {
        "title": "Hello",
        "starts_at": now - timezone.timedelta(hours=1),
        "ends_at": now + timezone.timedelta(hours=1),
        "is_active": True,
    }
    defaults.update(overrides)
    return SiteAnnouncement.objects.create(**defaults)


def test_active_returns_published_in_window(api_client):
    _mk(title="now-active")
    _mk(title="past", ends_at=timezone.now() - timezone.timedelta(minutes=10))
    _mk(title="future", starts_at=timezone.now() + timezone.timedelta(days=1))
    _mk(title="inactive", is_active=False)
    titles = [a["title"] for a in api_client.get(reverse("announcements-active")).json()["results"]]
    assert titles == ["now-active"]


def test_audience_filters_for_anonymous(api_client):
    _mk(title="for-all", audience=SiteAnnouncement.Audience.ALL)
    _mk(title="for-anon", audience=SiteAnnouncement.Audience.ANONYMOUS)
    _mk(title="for-streamers", audience=SiteAnnouncement.Audience.STREAMERS)
    titles = {a["title"] for a in api_client.get(reverse("announcements-active")).json()["results"]}
    assert titles == {"for-all", "for-anon"}


def test_audience_filters_for_viewer(auth_client_factory):
    _mk(title="for-all", audience=SiteAnnouncement.Audience.ALL)
    _mk(title="for-viewers", audience=SiteAnnouncement.Audience.VIEWERS)
    _mk(title="for-streamers", audience=SiteAnnouncement.Audience.STREAMERS)
    _mk(title="for-anon", audience=SiteAnnouncement.Audience.ANONYMOUS)
    client = auth_client_factory(UserFactory())  # viewer (pas de provisioning)
    titles = {a["title"] for a in client.get(reverse("announcements-active")).json()["results"]}
    assert titles == {"for-all", "for-viewers"}


def test_active_payload_contains_design_fields(api_client):
    _mk(
        title="Charity Day",
        level=SiteAnnouncement.Level.SUCCESS,
        display_mode=SiteAnnouncement.DisplayMode.POPUP,
        dismissible=True,
        cta_label="Découvrir",
        cta_url="https://example.com",
    )
    a = api_client.get(reverse("announcements-active")).json()["results"][0]
    assert a["level"] == "success"
    assert a["display_mode"] == "popup"
    assert a["dismissible"] is True
    assert a["cta_label"] == "Découvrir"
    assert a["cta_url"] == "https://example.com"
