"""Wave — init de paiement via l'API Wave Checkout.

Si `WAVE_API_KEY` n'est pas configurée, repli sur une confirmation immédiate
(mode dev/démo), comme le provider FAKE.
"""

from __future__ import annotations

import secrets

from django.conf import settings

from .base import PaymentProvider


class WaveProvider(PaymentProvider):
    name = "wave"

    def create_checkout(self, purchase) -> dict:
        if not settings.WAVE_API_KEY:
            return {
                "provider_ref": f"wave-demo-{secrets.token_hex(6)}",
                "checkout_url": None,
                "auto_confirm": True,
            }
        raise NotImplementedError("Wave configuré mais l'appel d'init n'est pas encore implémenté.")
