"""Contrat commun des fournisseurs de paiement."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PaymentProvider(ABC):
    name = "base"

    @abstractmethod
    def create_checkout(self, purchase) -> dict:
        """Retourne un dict : {provider_ref, checkout_url?, auto_confirm?}."""

    def is_simulated(self) -> bool:
        """True si le provider confirme sans encaissement réel (dev/démo).

        Un provider simulé est REFUSÉ hors dev, sauf `PAYMENTS_ALLOW_FAKE=1`
        (démo assumée) : sinon il distribuerait de l'Aura gratuite.
        """
        return False

    def verify_webhook(self, request) -> dict | None:
        """Valide un webhook et retourne un événement normalisé, ou None.

        Forme : {"event": "paid" | "refunded" | "disputed", "purchase_id"?,
        "payment_ref"?, "amount"?, "currency"?}.
        """
        return None
