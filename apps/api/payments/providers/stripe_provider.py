"""Fournisseur Stripe Checkout (carte). Actif si STRIPE_SECRET_KEY est posé.

Le checkout utilise le SDK Stripe ; la vérification du webhook est faite à la
main (HMAC-SHA256, schéma `Stripe-Signature`) — sans dépendance réseau, donc
testable hors-ligne et robuste même si le SDK évolue.

⚠️ Le FCFA (XOF/XAF) est une devise **sans décimale** chez Stripe : le montant
s'envoie tel quel (500 FCFA → 500), pas ×100.
"""

from __future__ import annotations

import decimal
import hashlib
import hmac
import json
import logging
import time

from django.conf import settings

from .base import PaymentProvider

logger = logging.getLogger(__name__)

# Tolérance anti-rejeu sur l'horodatage de la signature (secondes).
SIGNATURE_TOLERANCE_S = 300

# Devises sans subdivision chez Stripe (extrait pertinent pour la zone FCFA).
ZERO_DECIMAL_CURRENCIES = frozenset(
    {
        "xof",
        "xaf",
        "bif",
        "clp",
        "djf",
        "gnf",
        "jpy",
        "kmf",
        "krw",
        "mga",
        "pyg",
        "rwf",
        "ugx",
        "vnd",
        "vuv",
        "xpf",
    }
)


def stripe_amount(amount: decimal.Decimal | int | str, currency: str) -> int:
    """Montant en plus petite unité Stripe pour la devise donnée."""
    value = decimal.Decimal(str(amount))
    if currency.lower() in ZERO_DECIMAL_CURRENCIES:
        return int(value.quantize(decimal.Decimal("1")))
    return int((value * 100).quantize(decimal.Decimal("1")))


class StripeProvider(PaymentProvider):
    name = "stripe"

    def create_checkout(self, purchase) -> dict:
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": purchase.currency.lower(),
                        "product_data": {"name": f"{purchase.credits} Aura"},
                        "unit_amount": stripe_amount(purchase.fiat_amount, purchase.currency),
                    },
                    "quantity": 1,
                }
            ],
            success_url=f"{settings.FRONTEND_URL}/wallet?paid=1&purchase={purchase.id}",
            cancel_url=f"{settings.FRONTEND_URL}/wallet?canceled=1&purchase={purchase.id}",
            metadata={"purchase_id": str(purchase.id)},
        )
        return {"provider_ref": session.id, "checkout_url": session.url, "auto_confirm": False}

    def verify_webhook(self, request) -> dict | None:
        secret = settings.STRIPE_WEBHOOK_SECRET
        if not secret:
            logger.warning("stripe webhook: STRIPE_WEBHOOK_SECRET manquant")
            return None
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        body = request.body  # bytes bruts (indispensables pour la signature)
        if not self._verify_signature(body, sig_header, secret):
            logger.warning("stripe webhook: signature invalide")
            return None
        try:
            event = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        etype = event.get("type")
        obj = (event.get("data") or {}).get("object") or {}
        if etype == "checkout.session.completed":
            if obj.get("payment_status") not in (None, "paid"):
                # Paiement asynchrone non encore encaissé : on attend.
                return {"event": "ignored"}
            meta = obj.get("metadata") or {}
            return {
                "event": "paid",
                "purchase_id": meta.get("purchase_id"),
                "payment_ref": obj.get("payment_intent") or "",
                "amount": obj.get("amount_total"),
                "currency": (obj.get("currency") or "").lower(),
            }
        if etype == "charge.refunded":
            return {"event": "refunded", "payment_ref": obj.get("payment_intent") or ""}
        if etype == "charge.dispute.created":
            return {"event": "disputed", "payment_ref": obj.get("payment_intent") or ""}
        return {"event": "ignored"}

    @staticmethod
    def _verify_signature(payload: bytes, sig_header: str, secret: str) -> bool:
        timestamp: str | None = None
        signatures: list[str] = []
        for item in sig_header.split(","):
            key, _, value = item.strip().partition("=")
            if key == "t":
                timestamp = value
            elif key == "v1":
                signatures.append(value)
        if not timestamp or not signatures:
            return False
        try:
            if abs(time.time() - int(timestamp)) > SIGNATURE_TOLERANCE_S:
                return False
        except ValueError:
            return False
        signed_payload = f"{timestamp}.".encode() + payload
        expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
        return any(hmac.compare_digest(expected, sig) for sig in signatures)
