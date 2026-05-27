"""Fournisseur FAKE : confirme instantanément (dev/tests, aucune clé requise)."""

from __future__ import annotations

import secrets

from .base import PaymentProvider


class FakeProvider(PaymentProvider):
    name = "fake"

    def create_checkout(self, purchase) -> dict:  # noqa: ARG002
        return {
            "provider_ref": f"fake-{secrets.token_hex(8)}",
            "checkout_url": None,
            "auto_confirm": True,
        }
