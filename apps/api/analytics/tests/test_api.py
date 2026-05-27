"""Tests analytics : résumé streamer + overview admin."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel
from channels_app.services import mark_live, mark_offline

pytestmark = pytest.mark.django_db


def test_my_analytics_requires_auth(api_client):
    assert api_client.get(reverse("analytics-me")).status_code == 401


def test_my_analytics_counts_sessions(auth_client_factory):
    user = UserFactory()
    channel = Channel.objects.get(user=user)
    mark_live(channel)
    mark_offline(channel)
    data = auth_client_factory(user).get(reverse("analytics-me")).json()
    assert data["sessions_total"] == 1
    assert data["follower_count"] == 0


def test_overview_forbidden_for_non_admin(auth_client_factory):
    assert auth_client_factory(UserFactory()).get(reverse("analytics-overview")).status_code == 403


def test_overview_ok_for_admin(auth_client_factory):
    admin = UserFactory(is_staff=True)
    data = auth_client_factory(admin).get(reverse("analytics-overview")).json()
    assert "dau" in data and "mau" in data and "top_streamers" in data
    assert data["users_total"] >= 1
