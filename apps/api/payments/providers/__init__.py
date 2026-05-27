"""Sélection du fournisseur de paiement (couche d'abstraction)."""

from __future__ import annotations

from django.conf import settings

from .base import PaymentProvider
from .fake import FakeProvider
from .mobile_money import MobileMoneyProvider
from .stripe_provider import StripeProvider

_REGISTRY = {
    "fake": FakeProvider,
    "stripe": StripeProvider,
    "mobile_money": MobileMoneyProvider,
}


def get_provider_name() -> str:
    name = getattr(settings, "PAYMENTS_PROVIDER", "fake")
    # Repli sur FAKE si Stripe demandé mais non configuré.
    if name == "stripe" and not settings.STRIPE_SECRET_KEY:
        return "fake"
    return name if name in _REGISTRY else "fake"


def get_provider(name: str | None = None) -> PaymentProvider:
    return _REGISTRY[name or get_provider_name()]()


__all__ = ["PaymentProvider", "get_provider", "get_provider_name"]
