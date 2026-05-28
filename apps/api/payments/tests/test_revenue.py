"""Tests v2.4 : règles de commission (split), retraits admin, transactions, history."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User
from channels_app.models import Channel
from payments import services
from payments.models import FeeRule, LedgerEntry, Payout

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
    channel = Channel.objects.get(user=streamer)
    services.create_purchase(fan, 200)
    tip = services.send_tip(fan, channel.slug, 100)
    assert tip.platform_fee == 20
    assert tip.creator_share == 80


def test_resolve_payout_fail_refunds_user():
    user = UserFactory()
    services.create_purchase(user, 500)
    payout = services.request_payout(user, 300)
    assert services.get_wallet(user).aura_balance == 200
    admin = UserFactory()
    services.resolve_payout(admin, payout, "fail")
    payout.refresh_from_db()
    assert payout.status == Payout.Status.FAILED
    assert services.get_wallet(user).aura_balance == 500


def test_resolve_payout_paid_then_locked():
    user = UserFactory()
    services.create_purchase(user, 500)
    payout = services.request_payout(user, 100)
    admin = UserFactory()
    services.resolve_payout(admin, payout, "paid")
    payout.refresh_from_db()
    assert payout.status == Payout.Status.PAID
    with pytest.raises(services.PaymentError):
        services.resolve_payout(admin, payout, "paid")


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
