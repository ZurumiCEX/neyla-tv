"""Tests vérification de signature du webhook Stripe (HMAC, sans réseau)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest
from django.test import RequestFactory, override_settings

from payments.providers.stripe_provider import StripeProvider

SECRET = "whsec_test_secret"


def _signed_request(body: dict, secret: str = SECRET, ts: int | None = None):
    raw = json.dumps(body).encode("utf-8")
    timestamp = ts if ts is not None else int(time.time())
    signed = f"{timestamp}.".encode() + raw
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return RequestFactory().post(
        "/api/payments/webhook/stripe",
        data=raw,
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=f"t={timestamp},v1={sig}",
    )


EVENT = {
    "type": "checkout.session.completed",
    "data": {"object": {"metadata": {"purchase_id": "42"}}},
}


@override_settings(STRIPE_WEBHOOK_SECRET=SECRET)
def test_valid_signature_returns_purchase_id():
    result = StripeProvider().verify_webhook(_signed_request(EVENT))
    assert result["event"] == "paid"
    assert result["purchase_id"] == "42"


@override_settings(STRIPE_WEBHOOK_SECRET=SECRET)
def test_wrong_secret_rejected():
    req = _signed_request(EVENT, secret="whsec_wrong")
    assert StripeProvider().verify_webhook(req) is None


@override_settings(STRIPE_WEBHOOK_SECRET=SECRET)
def test_stale_timestamp_rejected():
    req = _signed_request(EVENT, ts=int(time.time()) - 10_000)
    assert StripeProvider().verify_webhook(req) is None


@override_settings(STRIPE_WEBHOOK_SECRET="")
def test_missing_secret_returns_none():
    assert StripeProvider().verify_webhook(_signed_request(EVENT)) is None


@override_settings(STRIPE_WEBHOOK_SECRET=SECRET)
def test_other_event_type_ignored():
    other = {"type": "payment_intent.created", "data": {"object": {}}}
    assert StripeProvider().verify_webhook(_signed_request(other)) == {"event": "ignored"}


@pytest.mark.parametrize("header", ["", "t=123", "v1=abc", "garbage"])
@override_settings(STRIPE_WEBHOOK_SECRET=SECRET)
def test_malformed_signature_header_rejected(header):
    req = RequestFactory().post(
        "/api/payments/webhook/stripe",
        data=json.dumps(EVENT).encode(),
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE=header,
    )
    assert StripeProvider().verify_webhook(req) is None


# --- Montants FCFA (devise sans décimale) & flux webhook complet ---


def test_xof_is_zero_decimal_for_stripe():
    from payments.providers.stripe_provider import stripe_amount

    assert stripe_amount("500", "XOF") == 500  # pas 50 000
    assert stripe_amount("12.50", "EUR") == 1250


def _stripe_purchase(credits: int = 100):
    from accounts.factories import UserFactory
    from payments.models import Purchase

    return Purchase.objects.create(
        user=UserFactory(), credits=credits, fiat_amount=credits * 5, provider="stripe"
    )


def _paid_event(purchase, amount=None, currency="xof"):
    return {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"purchase_id": str(purchase.id)},
                "payment_status": "paid",
                "payment_intent": "pi_123",
                "amount_total": amount if amount is not None else int(purchase.fiat_amount),
                "currency": currency,
            }
        },
    }


@pytest.mark.django_db
@override_settings(STRIPE_WEBHOOK_SECRET=SECRET)
def test_replayed_webhook_credits_once(client):
    from payments import services

    purchase = _stripe_purchase()
    body = _paid_event(purchase)
    for _ in range(2):
        req = _signed_request(body)
        resp = client.post(
            "/api/payments/webhook/stripe",
            data=req.body,
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE=req.META["HTTP_STRIPE_SIGNATURE"],
        )
        assert resp.status_code == 200
    assert services.get_wallet(purchase.user).aura_balance == 100


@pytest.mark.django_db
@override_settings(STRIPE_WEBHOOK_SECRET=SECRET)
def test_amount_mismatch_marks_purchase_failed():
    from payments import services
    from payments.models import Purchase

    purchase = _stripe_purchase()
    event = StripeProvider().verify_webhook(_signed_request(_paid_event(purchase, amount=1)))
    services.handle_provider_event("stripe", event)
    purchase.refresh_from_db()
    assert purchase.status == Purchase.Status.FAILED
    assert services.get_wallet(purchase.user).aura_balance == 0


@pytest.mark.django_db
@override_settings(STRIPE_WEBHOOK_SECRET=SECRET)
def test_refund_event_reverses_purchase():
    from payments import services
    from payments.models import Purchase

    purchase = _stripe_purchase()
    services.handle_provider_event(
        "stripe", StripeProvider().verify_webhook(_signed_request(_paid_event(purchase)))
    )
    refund = {"type": "charge.refunded", "data": {"object": {"payment_intent": "pi_123"}}}
    services.handle_provider_event(
        "stripe", StripeProvider().verify_webhook(_signed_request(refund))
    )
    purchase.refresh_from_db()
    assert purchase.status == Purchase.Status.REFUNDED
    assert services.get_wallet(purchase.user).aura_balance == 0


@pytest.mark.django_db
def test_unknown_provider_webhook_is_404(client):
    resp = client.post("/api/payments/webhook/bogus", data=b"{}", content_type="application/json")
    assert resp.status_code == 404
