"""Tests idempotence des opérations monétaires sensibles (achat, tip, payout)."""

from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from channels_app.models import Channel
from payments import services
from payments.models import Payout, Purchase, Tip

pytestmark = pytest.mark.django_db


def test_create_purchase_is_idempotent():
    user = UserFactory()
    p1, _ = services.create_purchase(user, 500, idempotency_key="abc")
    p2, _ = services.create_purchase(user, 500, idempotency_key="abc")
    assert p1.id == p2.id
    assert Purchase.objects.filter(user=user).count() == 1
    # Le wallet n'est crédité qu'une fois (FAKE auto-confirm).
    assert services.get_wallet(user).aura_balance == 500


def test_create_purchase_without_key_creates_each_time():
    user = UserFactory()
    services.create_purchase(user, 100)
    services.create_purchase(user, 100)
    assert Purchase.objects.filter(user=user).count() == 2


def test_send_tip_is_idempotent():
    fan = UserFactory()
    channel = Channel.objects.get(user=UserFactory())
    services.create_purchase(fan, 500)
    t1 = services.send_tip(fan, channel.slug, 50, idempotency_key="tip-1")
    t2 = services.send_tip(fan, channel.slug, 50, idempotency_key="tip-1")
    assert t1.id == t2.id
    assert Tip.objects.filter(from_user=fan).count() == 1
    # Débité une seule fois : 500 - 50.
    assert services.get_wallet(fan).aura_balance == 450


def test_request_payout_is_idempotent():
    user = UserFactory()
    services.create_purchase(user, 500)
    p1 = services.request_payout(user, 100, idempotency_key="po-1")
    p2 = services.request_payout(user, 100, idempotency_key="po-1")
    assert p1.id == p2.id
    assert Payout.objects.filter(user=user).count() == 1
    assert services.get_wallet(user).aura_balance == 400


def test_purchase_endpoint_honors_header(auth_client_factory):
    from django.urls import reverse

    user = UserFactory()
    client = auth_client_factory(user)
    headers = {"HTTP_IDEMPOTENCY_KEY": "hdr-1"}
    r1 = client.post(reverse("payments-purchase"), {"credits": 200}, format="json", **headers)
    r2 = client.post(reverse("payments-purchase"), {"credits": 200}, format="json", **headers)
    assert r1.status_code == 201 and r2.status_code == 201
    assert Purchase.objects.filter(user=user).count() == 1
