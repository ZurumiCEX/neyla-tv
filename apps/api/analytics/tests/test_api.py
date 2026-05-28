"""Tests analytics : résumé streamer + overview admin."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User
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
    admin = UserFactory(role=User.Role.ADMIN)
    data = auth_client_factory(admin).get(reverse("analytics-overview")).json()
    assert "dau" in data and "mau" in data and "top_streamers" in data
    assert data["users_total"] >= 1


def test_dashboard_returns_revenue_series(auth_client_factory):
    admin = UserFactory(role=User.Role.ADMIN)
    data = auth_client_factory(admin).get(reverse("admin-dashboard")).json()
    assert "overview" in data
    assert "series" in data["revenue"] and "totals" in data["revenue"]
    assert len(data["revenue"]["series"]) == 14


def test_dashboard_forbidden_for_non_admin(auth_client_factory):
    assert auth_client_factory(UserFactory()).get(reverse("admin-dashboard")).status_code == 403


def test_monitoring_forbidden_for_non_admin(auth_client_factory):
    assert auth_client_factory(UserFactory()).get(reverse("admin-monitoring")).status_code == 403


def test_monitoring_ok_for_admin(auth_client_factory):
    admin = UserFactory(role=User.Role.ADMIN)
    streamer = UserFactory()
    mark_live(Channel.objects.get(user=streamer))
    data = auth_client_factory(admin).get(reverse("admin-monitoring")).json()
    assert data["live_now"] >= 1
    assert "services" in data and "database" in data["services"]
    assert any(c["username"] == streamer.username for c in data["live_channels"])
