"""Orange Money — init de paiement via l'API Orange Money Web Payment.

Si `ORANGE_MONEY_API_KEY` n'est pas configurée, repli sur une confirmation
immédiate (mode dev/démo), comme le provider FAKE — le reste du système
(wallet, ledger, crédit à la confirmation) est agnostique du provider.
"""

from __future__ import annotations

import secrets

from django.conf import settings

from .base import PaymentProvider


class OrangeMoneyProvider(PaymentProvider):
    name = "orange_money"

    def create_checkout(self, purchase) -> dict:
        if not settings.ORANGE_MONEY_API_KEY:
            # Dev/démo : pas de clé → on confirme tout de suite.
            return {
                "provider_ref": f"om-demo-{secrets.token_hex(6)}",
                "checkout_url": None,
                "auto_confirm": True,
            }
        # Intégration réelle à brancher (init paiement → URL de redirection OM).
        raise NotImplementedError(
            "Orange Money configuré mais l'appel d'init n'est pas encore implémenté."
        )
