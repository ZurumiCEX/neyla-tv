"""Fournisseur Stripe Checkout (carte). Actif si STRIPE_SECRET_KEY est posé."""

from __future__ import annotations

import logging

from django.conf import settings

from .base import PaymentProvider

logger = logging.getLogger(__name__)


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
                        "unit_amount": int(purchase.fiat_amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            success_url=f"{settings.FRONTEND_URL}/wallet?paid=1",
            cancel_url=f"{settings.FRONTEND_URL}/wallet?canceled=1",
            metadata={"purchase_id": str(purchase.id)},
        )
        return {"provider_ref": session.id, "checkout_url": session.url, "auto_confirm": False}

    def verify_webhook(self, request) -> dict | None:
        import stripe

        sig = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        try:
            event = stripe.Webhook.construct_event(
                request.body, sig, settings.STRIPE_WEBHOOK_SECRET
            )
        except Exception:
            logger.warning("stripe webhook: signature invalide")
            return None
        if event.get("type") == "checkout.session.completed":
            meta = event["data"]["object"].get("metadata") or {}
            return {"purchase_id": meta.get("purchase_id")}
        return None
