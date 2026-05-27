"""Conversion d'affichage XOF → EUR/USD.

XOF (FCFA) est la devise de la plateforme. L'EUR utilise la **parité fixe**
officielle (1 EUR = 655,957 XOF). L'USD utilise un taux **configurable** (admin),
sans dépendance à une API externe.
"""

from __future__ import annotations

import decimal

from django.conf import settings

CENTS = decimal.Decimal("0.01")


def _rate(name: str, default: str) -> decimal.Decimal:
    return decimal.Decimal(str(getattr(settings, name, default)))


def to_eur(xof: decimal.Decimal) -> decimal.Decimal:
    return (decimal.Decimal(xof) / _rate("EUR_XOF_RATE", "655.957")).quantize(CENTS)


def to_usd(xof: decimal.Decimal) -> decimal.Decimal:
    return (decimal.Decimal(xof) / _rate("USD_XOF_RATE", "600")).quantize(CENTS)


def equivalents(xof: decimal.Decimal) -> dict:
    """{xof, eur, usd} en chaînes (pour affichage / API)."""
    xof = decimal.Decimal(xof)
    return {
        "xof": str(xof.quantize(decimal.Decimal("1"))),
        "eur": str(to_eur(xof)),
        "usd": str(to_usd(xof)),
    }
