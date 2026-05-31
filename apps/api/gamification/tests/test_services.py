"""Tests gamification : attribution idempotente, paliers followers, notif, endpoint."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from gamification import services
from gamification.models import Achievement, UserAchievement
from notifications.models import Notification

pytestmark = pytest.mark.django_db


def test_award_is_idempotent_and_notifies():
    user = UserFactory()
    services.check_and_award(user, "first_login")
    services.check_and_award(user, "first_login")
    assert UserAchievement.objects.filter(user=user).count() == 1
    assert (
        Notification.objects.filter(recipient=user, type=Notification.Type.ACHIEVEMENT).count() == 1
    )


def test_follow_threshold_awards_50_only():
    user = UserFactory()
    services.check_and_award(user, "follow_received", follower_count=50)
    keys = set(UserAchievement.objects.filter(user=user).values_list("achievement__key", flat=True))
    assert keys == {"followers_50"}


def test_follow_threshold_awards_both_at_100():
    user = UserFactory()
    services.check_and_award(user, "follow_received", follower_count=120)
    keys = set(UserAchievement.objects.filter(user=user).values_list("achievement__key", flat=True))
    assert keys == {"followers_50", "followers_100"}


def test_check_and_award_never_raises_on_unknown_event():
    user = UserFactory()
    services.check_and_award(user, "does_not_exist")
    assert UserAchievement.objects.filter(user=user).count() == 0


def test_achievements_endpoint_lists_catalog(auth_client_factory):
    user = UserFactory()
    services.check_and_award(user, "first_login")
    resp = auth_client_factory(user).get(reverse("achievements-list"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == len(services.CATALOG)
    assert body["unlocked"] == 1
    first = next(a for a in body["results"] if a["key"] == "first_login")
    assert first["unlocked"] is True
    assert "criteria" in first and "icon_url" in first  # champs enrichis exposés
    assert Achievement.objects.count() == len(services.CATALOG)


def test_achievements_endpoint_hides_inactive(auth_client_factory):
    services.sync_catalog()
    Achievement.objects.filter(key="first_login").update(is_active=False)
    client = auth_client_factory(UserFactory())
    keys = [a["key"] for a in client.get(reverse("achievements-list")).json()["results"]]
    assert "first_login" not in keys


def test_user_achievements_public_returns_unlocked(api_client):
    user = UserFactory(username="showcase")
    services.check_and_award(user, "first_login")
    services.check_and_award(user, "tip_sent")
    resp = api_client.get(reverse("achievements-user", args=["showcase"]))
    assert resp.status_code == 200  # public (sans auth)
    body = resp.json()
    assert body["unlocked"] == 2
    keys = {a["key"] for a in body["results"]}
    assert {"first_login", "first_tip_sent"} <= keys


def test_user_achievements_unknown_user_empty(api_client):
    body = api_client.get(reverse("achievements-user", args=["ghost"])).json()
    assert body == {"results": [], "unlocked": 0}
