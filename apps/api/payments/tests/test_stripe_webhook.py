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
    assert result == {"purchase_id": "42"}


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
    assert StripeProvider().verify_webhook(_signed_request(other)) is None


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
