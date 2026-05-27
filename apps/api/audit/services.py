"""Helper d'audit : record(actor, action, target=instance, meta=...)."""

from __future__ import annotations

from .models import AuditEvent


def record(actor, action: str, target=None, meta: dict | None = None) -> AuditEvent:
    target_type = ""
    target_id = ""
    if target is not None:
        target_type = target.__class__.__name__
        target_id = str(getattr(target, "pk", "") or "")
    return AuditEvent.objects.create(
        actor=actor if getattr(actor, "pk", None) else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        meta=meta or {},
    )
