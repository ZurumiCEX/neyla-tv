"""Diffusion d'alertes temps réel vers l'overlay OBS (best-effort)."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


def send_overlay_alert(
    channel_id: int, kind: str, actor: str = "", amount: int | None = None
) -> None:
    """Pousse une alerte au groupe overlay de la chaîne. N'échoue jamais bruyamment."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        layer = get_channel_layer()
        if layer is None:
            return
        alert: dict = {"kind": kind, "actor": actor, "ts": int(time.time() * 1000)}
        if amount is not None:
            alert["amount"] = amount
        async_to_sync(layer.group_send)(
            f"overlay.{channel_id}", {"type": "overlay.alert", "alert": alert}
        )
    except Exception:  # noqa: BLE001
        logger.debug("overlay alert non délivrée", exc_info=True)
