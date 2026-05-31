"""Tests monétisation : achat (FAKE), tip 70/30, payout, soldes."""

from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from payments import services
from payments.models import Purchase, Tip, Wallet

pytestmark = pytest.mark.django_db


def test_conversion_equivalents(settings):
    settings.EUR_XOF_RATE = "655.957"
    settings.USD_XOF_RATE = "600"
    from payments import conversion

    eq = conversion.equivalents(655957)
    assert eq["xof"] == "655957"
    assert eq["eur"] == "1000.00"
    assert eq["usd"] == "1093.26"


def test_fake_purchase_credits_wallet():
    user = UserFactory()
    purchase, _ = services.create_purchase(user, 500)
    assert purchase.status == Purchase.Status.PAID
    assert Wallet.objects.get(user=user).aura_balance == 500


def test_confirm_purchase_is_idempotent():
    user = UserFactory()
    purchase, _ = services.create_purchase(user, 100)
    services.confirm_purchase(purchase)  # 2e fois
    assert Wallet.objects.get(user=user).aura_balance == 100


def test_tip_splits_70_30():
    sender = UserFactory()
    streamer = UserFactory(username="creator")
    services.create_purchase(sender, 100)
    tip = services.send_tip(sender, "creator", 10)
    assert tip.creator_share == 7
    assert tip.platform_fee == 3
    assert services.get_wallet(sender).aura_balance == 90
    assert services.get_wallet(streamer).aura_balance == 7


def test_tip_insufficient_balance():
    sender = UserFactory()
    UserFactory(username="creator2")
    with pytest.raises(services.InsufficientBalanceError):
        services.send_tip(sender, "creator2", 5)


def test_cannot_tip_self():
    user = UserFactory(username="self1")
    services.create_purchase(user, 50)
    with pytest.raises(services.PaymentError):
        services.send_tip(user, "self1", 5)


def test_payout_debits_wallet():
    user = UserFactory()
    services.create_purchase(user, 100)
    payout = services.request_payout(user, 60)
    assert payout.aura_amount == 60
    assert services.get_wallet(user).aura_balance == 40


def test_tip_endpoint(auth_client_factory):
    from django.urls import reverse

    sender = UserFactory()
    UserFactory(username="creator3")
    services.create_purchase(sender, 100)
    client = auth_client_factory(sender)
    resp = client.post(
        reverse("payments-tip"),
        {"channel_slug": "creator3", "aura_amount": 20},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["creator_share"] == 14
    assert Tip.objects.count() == 1


# --- Business model : commission d'achat 1% sur les streamers uniquement ---


def test_viewer_purchase_no_commission():
    """Un viewer (non streamer) achète : aucune commission, 1 Aura = 1 Aura."""
    from payments.models import FeeRule

    FeeRule.objects.get_or_create(
        product=FeeRule.Product.PURCHASE,
        defaults={"mode": FeeRule.Mode.PERCENTAGE, "value": 1, "is_active": True},
    )
    user = UserFactory()
    services.create_purchase(user, 1000)
    assert services.get_wallet(user).aura_balance == 1000


def test_streamer_purchase_takes_1pct_commission():
    """Un streamer approuvé subit 1% de commission sur ses achats."""
    from channels_app.models import Channel
    from channels_app.services import provision_channel
    from payments.models import FeeRule

    FeeRule.objects.get_or_create(
        product=FeeRule.Product.PURCHASE,
        defaults={"mode": FeeRule.Mode.PERCENTAGE, "value": 1, "is_active": True},
    )
    streamer = UserFactory()
    channel = Channel.objects.get(user=streamer)
    provision_channel(channel)  # is_provisioned = True
    services.create_purchase(streamer, 1000)
    # 1% sur 1000 = 10 → crédit = 990
    assert services.get_wallet(streamer).aura_balance == 990
