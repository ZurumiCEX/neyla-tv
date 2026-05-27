"""Contrat commun des fournisseurs de paiement."""

from __future__ import annotations

from abc import ABC, abstractmethod


class PaymentProvider(ABC):
    name = "base"

    @abstractmethod
    def create_checkout(self, purchase) -> dict:
        """Retourne un dict : {provider_ref, checkout_url?, auto_confirm?}."""

    def verify_webhook(self, request) -> dict | None:
        """Valide un webhook et retourne {purchase_id} ou None."""
        return None
