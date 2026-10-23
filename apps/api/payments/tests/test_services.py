"""Tests monétisation : achat (FAKE), tip 70/30, payout, soldes."""

from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from channels_app.testing import provisioned_channel
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
    provisioned_channel(streamer)
    services.create_purchase(sender, 100)
    tip = services.send_tip(sender, "creator", 10)
    assert tip.creator_share == 7
    assert tip.platform_fee == 3
    assert services.get_wallet(sender).aura_balance == 90
    assert services.get_wallet(streamer).aura_balance == 7


def test_tip_insufficient_balance():
    sender = UserFactory()
    provisioned_channel(UserFactory(username="creator2"))
    with pytest.raises(services.InsufficientBalanceError):
        services.send_tip(sender, "creator2", 50)


def test_tip_below_minimum_refused():
    sender = UserFactory()
    provisioned_channel(UserFactory(username="creatormin"))
    services.create_purchase(sender, 100)
    with pytest.raises(services.PaymentError):
        services.send_tip(sender, "creatormin", 5)


def test_tip_to_unapproved_channel_refused():
    """Une chaîne non provisionnée (non approuvée) ne peut pas encaisser."""
    sender = UserFactory()
    UserFactory(username="notstreamer")
    services.create_purchase(sender, 100)
    with pytest.raises(services.PaymentError):
        services.send_tip(sender, "notstreamer", 20)


def test_small_tip_fee_rounds_half_up():
    sender = UserFactory()
    provisioned_channel(UserFactory(username="creatorr"))
    services.create_purchase(sender, 100)
    tip = services.send_tip(sender, "creatorr", 15)  # 30 % de 15 = 4,5 → 5
    assert (tip.creator_share, tip.platform_fee) == (10, 5)


def test_cannot_tip_self():
    user = UserFactory(username="self1")
    services.create_purchase(user, 50)
    with pytest.raises(services.PaymentError):
        services.send_tip(user, "self1", 5)


def test_payout_debits_wallet(earning_streamer):
    user = earning_streamer(100)  # 70 gagnés
    payout = services.create_payout(user, 60)
    assert payout.aura_amount == 60
    assert services.get_wallet(user).aura_balance == 10


def test_purchased_aura_is_never_withdrawable(earning_streamer):
    user = earning_streamer(100)  # 70 gagnés
    services.create_purchase(user, 1000)  # 990 achetés (1 % streamer)
    assert services.withdrawable_balance(user) == 70
    with pytest.raises(services.InsufficientBalanceError):
        services.create_payout(user, 500)


def test_legacy_payout_endpoint_removed(auth_client_factory):
    resp = auth_client_factory(UserFactory()).post(
        "/api/payments/payout", {"aura_amount": 10}, format="json"
    )
    assert resp.status_code == 404


def test_simulated_provider_refused_outside_demo(settings):
    settings.PAYMENTS_ALLOW_FAKE = False
    with pytest.raises(services.PaymentError):
        services.create_purchase(UserFactory(), 100)


def test_refund_claws_back_and_holds_payouts_when_spent():
    from payments.models import LedgerEntry
    from safety.models import RiskEvent

    buyer = UserFactory()
    provisioned_channel(UserFactory(username="refundee"))
    purchase, _ = services.create_purchase(buyer, 100)
    services.send_tip(buyer, "refundee", 80)  # reste 20
    services.reverse_purchase(purchase, disputed=True)
    purchase.refresh_from_db()
    wallet = services.get_wallet(buyer)
    assert purchase.status == Purchase.Status.DISPUTED
    assert wallet.aura_balance == 0
    assert wallet.payout_hold is True
    assert LedgerEntry.objects.get(wallet=wallet, kind="refund").amount == -20
    assert RiskEvent.objects.filter(user=buyer, kind="chargeback").exists()
    # Rejouer le remboursement ne reprend rien de plus.
    services.reverse_purchase(purchase)
    assert LedgerEntry.objects.filter(wallet=wallet, kind="refund").count() == 1


def test_wallets_reconcile_with_ledger(earning_streamer):
    user = earning_streamer(500)
    services.create_payout(user, 100)
    assert services.wallet_drift() == []


def test_tip_endpoint(auth_client_factory):
    from django.urls import reverse

    sender = UserFactory()
    provisioned_channel(UserFactory(username="creator3"))
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
