"""Sélection du fournisseur de paiement (couche d'abstraction)."""

from __future__ import annotations

from django.conf import settings

from .base import PaymentProvider
from .fake import FakeProvider
from .mobile_money import MobileMoneyProvider
from .orange_money import OrangeMoneyProvider
from .stripe_provider import StripeProvider
from .wave import WaveProvider

_REGISTRY = {
    "fake": FakeProvider,
    "stripe": StripeProvider,
    "mobile_money": MobileMoneyProvider,
    "orange_money": OrangeMoneyProvider,
    "wave": WaveProvider,
}

# Méthodes de paiement proposées côté client (mappées vers un provider concret).
PAYMENT_METHODS = ("card", "orange_money", "wave")


def method_to_provider(method: str) -> str:
    """Traduit une méthode UI (card/orange_money/wave) en nom de provider."""
    if method == "card":
        return "stripe" if settings.STRIPE_SECRET_KEY else "fake"
    if method in ("orange_money", "wave"):
        return method
    return get_provider_name()


def get_provider_name() -> str:
    name = getattr(settings, "PAYMENTS_PROVIDER", "fake")
    # Repli sur FAKE si Stripe demandé mais non configuré.
    if name == "stripe" and not settings.STRIPE_SECRET_KEY:
        return "fake"
    return name if name in _REGISTRY else "fake"


def get_provider(name: str | None = None) -> PaymentProvider:
    return _REGISTRY[name or get_provider_name()]()


__all__ = [
    "PAYMENT_METHODS",
    "PaymentProvider",
    "get_provider",
    "get_provider_name",
    "method_to_provider",
]
