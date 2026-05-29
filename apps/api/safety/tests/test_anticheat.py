"""Tests anti-triche : vélocité tips/follows + endpoints risque."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User
from channels_app.models import Channel
from payments import services as pay
from safety import anticheat
from safety.models import RiskEvent

pytestmark = pytest.mark.django_db


def test_tip_velocity_flagged():
    creator = UserFactory()
    channel = Channel.objects.get(user=creator)
    fan = UserFactory()
    pay.create_purchase(fan, 1000)
    for _ in range(anticheat.TIP_MAX_PER_WINDOW + 1):
        pay.send_tip(fan, channel.slug, 1)
    assert RiskEvent.objects.filter(user=fan, kind=RiskEvent.Kind.TIP_VELOCITY).exists()


def test_no_flag_under_threshold():
    creator = UserFactory()
    channel = Channel.objects.get(user=creator)
    fan = UserFactory()
    pay.create_purchase(fan, 1000)
    pay.send_tip(fan, channel.slug, 1)
    assert not RiskEvent.objects.filter(user=fan, kind=RiskEvent.Kind.TIP_VELOCITY).exists()


def test_follow_velocity_detector():
    follower = UserFactory()
    target = UserFactory()
    # Force le détecteur via création directe de follows.
    from social.models import Follow

    for _ in range(anticheat.FOLLOW_MAX_PER_WINDOW):
        Follow.objects.create(follower=follower, followee=UserFactory())
    anticheat.evaluate_follow(follower, target)
    assert RiskEvent.objects.filter(user=follower, kind=RiskEvent.Kind.FOLLOW_VELOCITY).exists()


def test_risk_events_endpoint_moderator_only(api_client, auth_client_factory):
    assert api_client.get(reverse("safety-risk-events")).status_code == 401
    assert auth_client_factory(UserFactory()).get(reverse("safety-risk-events")).status_code == 403


def test_moderator_resolves_risk(auth_client_factory):
    user = UserFactory()
    ev = anticheat.flag(user, RiskEvent.Kind.TIP_VELOCITY, RiskEvent.Severity.HIGH, {"count": 99})
    mod = UserFactory(role=User.Role.MODERATOR)
    client = auth_client_factory(mod)
    assert client.get(reverse("safety-risk-events")).status_code == 200
    resp = client.post(reverse("safety-risk-resolve", kwargs={"pk": ev.id}))
    assert resp.status_code == 200
    ev.refresh_from_db()
    assert ev.resolved is True


def test_overview(auth_client_factory):
    mod = UserFactory(role=User.Role.MODERATOR)
    data = auth_client_factory(mod).get(reverse("safety-overview")).json()
    assert "open_risk_events" in data and "pending_flags" in data
