"""Tests retrait : éligibilité streamer, solde retirable, OTP, frais."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel
from channels_app.services import provision_channel
from payments import services
from payments.models import PayoutOtp

pytestmark = pytest.mark.django_db


def _streamer():
    user = UserFactory()
    provision_channel(Channel.objects.get(user=user))
    return user


def test_only_streamer_can_start(auth_client_factory):
    user = UserFactory()  # non provisionné
    services.create_purchase(user, 500)  # achat ≠ retirable
    resp = auth_client_factory(user).post(
        reverse("withdrawal-start"), {"aura_amount": 100}, format="json"
    )
    assert resp.status_code == 400


def test_withdrawable_excludes_purchases():
    user = _streamer()
    services.create_purchase(user, 1000)  # achat → non retirable
    assert services.withdrawable_balance(user) == 0


def test_withdrawable_counts_tips_and_subs():
    creator = _streamer()
    channel = Channel.objects.get(user=creator)
    fan = UserFactory()
    services.create_purchase(fan, 500)
    services.send_tip(fan, channel.slug, 100)  # creator reçoit 70 (split 70/30)
    assert services.withdrawable_balance(creator) == 70


def test_quote_applies_fee():
    q = services.withdrawal_quote(100)
    assert q["fee_pct"] == 30
    assert q["fee_aura"] == 30
    assert q["net_aura"] == 70


def test_otp_flow_creates_payout(auth_client_factory):
    creator = _streamer()
    channel = Channel.objects.get(user=creator)
    fan = UserFactory()
    services.create_purchase(fan, 500)
    services.send_tip(fan, channel.slug, 100)  # +70 retirable

    client = auth_client_factory(creator)
    start = client.post(reverse("withdrawal-start"), {"aura_amount": 70}, format="json")
    assert start.status_code == 200
    otp = PayoutOtp.objects.filter(user=creator, consumed=False).latest("created_at")
    # On ne connaît pas le code en clair : on en force un connu pour le test.
    otp.code_hash = services._hash_otp("123456")
    otp.save(update_fields=["code_hash"])

    confirm = client.post(reverse("withdrawal-confirm"), {"code": "123456"}, format="json")
    assert confirm.status_code == 201
    assert confirm.json()["aura_amount"] == 70


def test_confirm_rejects_bad_code(auth_client_factory):
    creator = _streamer()
    channel = Channel.objects.get(user=creator)
    fan = UserFactory()
    services.create_purchase(fan, 500)
    services.send_tip(fan, channel.slug, 100)
    client = auth_client_factory(creator)
    client.post(reverse("withdrawal-start"), {"aura_amount": 70}, format="json")
    resp = client.post(reverse("withdrawal-confirm"), {"code": "000000"}, format="json")
    assert resp.status_code == 400


def test_eligibility_endpoint(auth_client_factory):
    creator = _streamer()
    data = auth_client_factory(creator).get(reverse("withdrawal-eligibility")).json()
    assert data["is_streamer"] is True
    assert data["fee_pct"] == 30
    assert "withdrawable" in data


def test_purchase_accepts_method(auth_client_factory):
    user = UserFactory()
    resp = auth_client_factory(user).post(
        reverse("payments-purchase"), {"credits": 100, "method": "wave"}, format="json"
    )
    assert resp.status_code == 201
