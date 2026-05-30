"""Tests revenus créateur consolidés (tips + abos + parrainage)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from analytics.services import creator_revenue
from channels_app.models import Channel
from payments import services as pay
from payments.models import LedgerEntry
from subscriptions import services as subs_services

pytestmark = pytest.mark.django_db


def _streamer_with_fan():
    channel = Channel.objects.get(user=UserFactory())
    subs_services.set_tier(channel, price_aura=100, perks=["Badge"])
    fan = UserFactory()
    pay.create_purchase(fan, 1000)
    return channel, fan


def test_creator_revenue_requires_auth(api_client):
    assert api_client.get(reverse("analytics-me-revenue")).status_code == 401


def test_creator_revenue_aggregates_tips_subs_referral(auth_client_factory):
    channel, fan = _streamer_with_fan()
    # Tip → SUB_EARNED via charge_subscription; tip_user via tip_user
    pay.send_tip(fan, channel.slug, aura_amount=50, message="bravo")
    subs_services.subscribe(fan, channel.slug)
    # Crédit direct de type REFERRAL pour simuler une récompense de parrainage.
    pay.grant_aura(channel.user, 25, LedgerEntry.Kind.REFERRAL, "referral:test")

    client = auth_client_factory(channel.user)
    resp = client.get(reverse("analytics-me-revenue"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] == "day"
    assert data["totals"]["tips"] > 0
    assert data["totals"]["subs"] > 0
    assert data["totals"]["referral"] == 25
    assert data["totals"]["total"] == (
        data["totals"]["tips"] + data["totals"]["subs"] + data["totals"]["referral"]
    )
    assert "summary" in data and {"day", "week", "month"} <= set(data["summary"])
    assert "withdrawable" in data
    # Le pic de revenus du jour est dans la dernière entrée.
    assert data["series"][-1]["total"] > 0


def test_creator_revenue_supports_week_and_month_period():
    streamer = UserFactory()
    Channel.objects.get(user=streamer)
    pay.grant_aura(streamer, 30, LedgerEntry.Kind.REFERRAL, "ref:a")
    week = creator_revenue(streamer, period="week")
    month = creator_revenue(streamer, period="month")
    assert week["period"] == "week" and len(week["series"]) == 12
    assert month["period"] == "month" and len(month["series"]) == 12
    assert week["totals"]["referral"] == 30
    assert month["totals"]["referral"] == 30


def test_creator_revenue_invalid_period_falls_back_to_day(auth_client_factory):
    user = UserFactory()
    Channel.objects.get(user=user)
    client = auth_client_factory(user)
    resp = client.get(reverse("analytics-me-revenue"), {"period": "bogus"})
    assert resp.status_code == 200
    assert resp.json()["period"] == "day"
