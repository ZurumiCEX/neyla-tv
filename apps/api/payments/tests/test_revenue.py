"""Tests v2.4 : règles de commission (split), retraits admin, transactions, history."""

from __future__ import annotations

import pytest
from django.db.models import Sum
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User
from channels_app.testing import provisioned_channel
from payments import services
from payments.models import FeeRule, LedgerEntry, Payout, PlatformRevenue

pytestmark = pytest.mark.django_db


def test_split_falls_back_to_creator_share():
    creator_share, fee = services.split(100, FeeRule.Product.TIP)
    assert creator_share == 70
    assert fee == 30


def test_split_uses_active_percentage_rule():
    FeeRule.objects.create(product=FeeRule.Product.TIP, mode=FeeRule.Mode.PERCENTAGE, value=10)
    creator_share, fee = services.split(100, FeeRule.Product.TIP)
    assert fee == 10
    assert creator_share == 90


def test_split_uses_active_fixed_rule_capped():
    FeeRule.objects.create(product=FeeRule.Product.TIP, mode=FeeRule.Mode.FIXED, value=5)
    assert services.split(100, FeeRule.Product.TIP) == (95, 5)
    # Commission plafonnée au montant.
    assert services.split(3, FeeRule.Product.TIP) == (0, 3)


def test_tip_respects_fee_rule():
    FeeRule.objects.create(product=FeeRule.Product.TIP, mode=FeeRule.Mode.PERCENTAGE, value=20)
    fan = UserFactory()
    streamer = UserFactory()
    channel = provisioned_channel(streamer)
    services.create_purchase(fan, 200)
    tip = services.send_tip(fan, channel.slug, 100)
    assert tip.platform_fee == 20
    assert tip.creator_share == 80


def test_resolve_payout_fail_refunds_user(earning_streamer):
    from payments.models import LedgerEntry

    user = earning_streamer(1000)  # 700 gagnés
    payout = services.create_payout(user, 300)
    assert services.get_wallet(user).aura_balance == 400
    admin = UserFactory()
    services.resolve_payout(admin, payout, "fail")
    payout.refresh_from_db()
    assert payout.status == Payout.Status.FAILED
    assert services.get_wallet(user).aura_balance == 700
    # Le recrédit est une écriture dédiée, pas un « retrait » positif.
    assert LedgerEntry.objects.filter(
        wallet__user=user, kind=LedgerEntry.Kind.PAYOUT_REVERSAL, amount=300
    ).exists()
    # Les frais d'un retrait échoué ne sont jamais comptés en revenu.
    assert not PlatformRevenue.objects.filter(source="withdrawal").exists()


def test_resolve_payout_processing_then_paid_records_fee(earning_streamer):
    user = earning_streamer(1000)
    payout = services.create_payout(user, 100)
    admin = UserFactory()
    services.resolve_payout(admin, payout, "processing")
    services.resolve_payout(admin, payout, "paid")
    payout.refresh_from_db()
    assert payout.status == Payout.Status.PAID
    assert PlatformRevenue.objects.get(source="withdrawal").amount_aura == payout.fee_aura == 3
    with pytest.raises(services.PaymentError):
        services.resolve_payout(admin, payout, "paid")


def test_tip_and_subscription_fees_recorded_as_revenue():
    from subscriptions import services as subs

    fan = UserFactory()
    channel = provisioned_channel(UserFactory())
    subs.set_tier(channel, price_aura=100, perks=[])
    services.create_purchase(fan, 500)
    services.send_tip(fan, channel.slug, 100)
    subs.subscribe(fan, channel.slug)
    sources = dict(PlatformRevenue.objects.values_list("source").annotate(s=Sum("amount_aura")))
    assert sources == {"tip": 30, "subscription": 30}


def test_transactions_endpoint_requires_admin(auth_client_factory):
    fan = UserFactory()
    resp = auth_client_factory(fan).get(reverse("admin-transactions"))
    assert resp.status_code == 403


def test_transactions_endpoint_lists_for_admin(auth_client_factory):
    fan = UserFactory()
    services.create_purchase(fan, 100)
    admin = UserFactory(role=User.Role.ADMIN)
    resp = auth_client_factory(admin).get(reverse("admin-transactions"))
    assert resp.status_code == 200
    assert resp.json()["count"] >= 1


def test_fees_crud_admin(auth_client_factory):
    admin = UserFactory(role=User.Role.ADMIN)
    client = auth_client_factory(admin)
    created = client.post(
        reverse("admin-fees"),
        {"product": "tip", "mode": "percentage", "value": "15"},
        format="json",
    )
    assert created.status_code == 201
    fee_id = created.json()["id"]
    patched = client.patch(
        reverse("admin-fee-detail", kwargs={"pk": fee_id}),
        {"is_active": False},
        format="json",
    )
    assert patched.status_code == 200
    assert patched.json()["is_active"] is False


def test_history_endpoint_paginated(auth_client_factory):
    user = UserFactory()
    services.create_purchase(user, 100)
    resp = auth_client_factory(user).get(reverse("payments-history"))
    assert resp.status_code == 200
    body = resp.json()
    assert "results" in body
    assert any(e["kind"] == LedgerEntry.Kind.PURCHASE for e in body["results"])
