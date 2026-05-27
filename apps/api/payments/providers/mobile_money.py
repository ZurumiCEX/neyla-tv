"""Stub mobile money — agrégateur à brancher (CinetPay / Flutterwave / Paystack…).

Implémenter `create_checkout` (init de paiement) et `verify_webhook` (callback de
l'agrégateur) selon le provider retenu. Le reste du système (wallet, ledger,
crédit à la confirmation) est déjà prêt et agnostique du provider.
"""

from __future__ import annotations

from .base import PaymentProvider


class MobileMoneyProvider(PaymentProvider):
    name = "mobile_money"

    def create_checkout(self, purchase) -> dict:  # noqa: ARG002
        raise NotImplementedError(
            "Agrégateur mobile money non configuré (à décider : CinetPay/Flutterwave/...)."
        )
