"""Envoi de Web Push (VAPID) — best-effort, dégrade proprement si non configuré."""

from __future__ import annotations

import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)


def send_to_subscription(subscription, payload: dict) -> bool:
    """Envoie une notification à un abonnement. Supprime l'abonnement si expiré.

    Renvoie True si l'envoi a réussi.
    """
    if not is_configured():
        return False
    try:
        from pywebpush import WebPushException, webpush

        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"},
        )
        return True
    except WebPushException as exc:
        # 404/410 = abonnement révoqué côté navigateur → on le supprime.
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in (404, 410):
            subscription.delete()
        else:
            logger.warning("web push failed: %s", exc)
        return False
    except Exception:
        logger.exception("web push unexpected error")
        return False
