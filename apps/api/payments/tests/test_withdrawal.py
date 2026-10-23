"""Tests retrait : éligibilité streamer, solde retirable, OTP, frais."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.testing import provisioned_channel
from payments import services
from payments.models import PayoutOtp

pytestmark = pytest.mark.django_db


DEST = {"destination_provider": "wave", "destination_phone": "+221771234567"}


@pytest.fixture(autouse=True)
def _low_minimum(settings):
    settings.WITHDRAWAL_MIN_AURA = 10


def _streamer():
    user = UserFactory()
    provisioned_channel(user)
    return user


def test_only_streamer_can_start(auth_client_factory):
    user = UserFactory()  # non provisionné
    services.create_purchase(user, 500)  # achat ≠ retirable
    resp = auth_client_factory(user).post(
        reverse("withdrawal-start"), {"aura_amount": 100, **DEST}, format="json"
    )
    assert resp.status_code == 400


def test_withdrawable_excludes_purchases():
    user = _streamer()
    services.create_purchase(user, 1000)  # achat → non retirable
    assert services.withdrawable_balance(user) == 0


def test_withdrawable_counts_tips_and_subs():
    creator = _streamer()
    channel = provisioned_channel(creator)
    fan = UserFactory()
    services.create_purchase(fan, 500)
    services.send_tip(fan, channel.slug, 100)  # creator reçoit 70 (split 70/30)
    assert services.withdrawable_balance(creator) == 70


def test_quote_applies_processing_fee_only():
    """Frais de traitement (3 %), pas une 2e commission de 30 %."""
    q = services.withdrawal_quote(1000)
    assert q["fee_pct"] == 3
    assert q["fee_aura"] == 30
    assert q["net_aura"] == 970
    assert q["net_fiat"] == "4850"  # 970 × 5 FCFA


def test_quote_matches_created_payout(earning_streamer):
    user = earning_streamer(1000)
    quote = services.withdrawal_quote(333)
    payout = services.create_payout(user, 333)
    assert payout.fee_aura == quote["fee_aura"]
    assert str(int(payout.fiat_amount)) == quote["net_fiat"]


def test_minimum_withdrawal_enforced(earning_streamer, settings):
    user = earning_streamer(1000)
    settings.WITHDRAWAL_MIN_AURA = 500
    with pytest.raises(services.PaymentError):
        services.start_withdrawal(user, 100, "wave", "+221771234567")


def test_start_requires_valid_destination(earning_streamer):
    user = earning_streamer(1000)
    with pytest.raises(services.PaymentError):
        services.start_withdrawal(user, 100, "paypal", "+221771234567")
    with pytest.raises(services.PaymentError):
        services.start_withdrawal(user, 100, "wave", "abc")


def test_otp_is_single_use(earning_streamer):
    user = earning_streamer(1000)
    services.start_withdrawal(user, 100, "wave", "+221771234567")
    otp = PayoutOtp.objects.get(user=user, consumed=False)
    otp.code_hash = services._hash_otp("654321")
    otp.save(update_fields=["code_hash"])
    services.confirm_withdrawal(user, "654321")
    with pytest.raises(services.PaymentError):
        services.confirm_withdrawal(user, "654321")


def test_otp_not_sent_in_app(earning_streamer, mailoutbox):
    from notifications.models import Notification

    user = earning_streamer(1000)
    before = Notification.objects.filter(recipient=user).count()
    services.start_withdrawal(user, 100, "wave", "+221771234567")
    assert len(mailoutbox) == 1
    assert Notification.objects.filter(recipient=user).count() == before


def test_otp_flow_creates_payout(auth_client_factory):
    creator = _streamer()
    channel = provisioned_channel(creator)
    fan = UserFactory()
    services.create_purchase(fan, 500)
    services.send_tip(fan, channel.slug, 100)  # +70 retirable

    client = auth_client_factory(creator)
    start = client.post(reverse("withdrawal-start"), {"aura_amount": 70, **DEST}, format="json")
    assert start.status_code == 200
    otp = PayoutOtp.objects.filter(user=creator, consumed=False).latest("created_at")
    # On ne connaît pas le code en clair : on en force un connu pour le test.
    otp.code_hash = services._hash_otp("123456")
    otp.save(update_fields=["code_hash"])

    confirm = client.post(reverse("withdrawal-confirm"), {"code": "123456"}, format="json")
    assert confirm.status_code == 201
    body = confirm.json()
    assert body["aura_amount"] == 70
    assert body["destination_provider"] == "wave"
    assert body["fee_aura"] == 2  # 3 % de 70 = 2,1 → 2


def test_confirm_rejects_bad_code(auth_client_factory):
    creator = _streamer()
    channel = provisioned_channel(creator)
    fan = UserFactory()
    services.create_purchase(fan, 500)
    services.send_tip(fan, channel.slug, 100)
    client = auth_client_factory(creator)
    client.post(reverse("withdrawal-start"), {"aura_amount": 70, **DEST}, format="json")
    resp = client.post(reverse("withdrawal-confirm"), {"code": "000000"}, format="json")
    assert resp.status_code == 400


def test_eligibility_endpoint(auth_client_factory):
    creator = _streamer()
    data = auth_client_factory(creator).get(reverse("withdrawal-eligibility")).json()
    assert data["is_streamer"] is True
    assert data["fee_pct"] == 3
    assert data["min_aura"] == 10
    assert "withdrawable" in data


def test_purchase_accepts_method(auth_client_factory):
    user = UserFactory()
    resp = auth_client_factory(user).post(
        reverse("payments-purchase"), {"credits": 100, "method": "wave"}, format="json"
    )
    assert resp.status_code == 201
