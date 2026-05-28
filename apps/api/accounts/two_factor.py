"""Logique métier 2FA : setup, activation, codes de secours, vérification."""

from __future__ import annotations

import hashlib
import secrets

from django.utils import timezone

from . import totp
from .models import TwoFactor

RECOVERY_CODE_COUNT = 10


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()


def _generate_recovery_codes() -> list[str]:
    codes = []
    for _ in range(RECOVERY_CODE_COUNT):
        raw = secrets.token_hex(4)
        codes.append(f"{raw[:4]}-{raw[4:]}")
    return codes


def is_enabled(user) -> bool:
    tf = getattr(user, "two_factor", None)
    return bool(tf and tf.enabled)


def begin_setup(user) -> TwoFactor:
    """Crée/rafraîchit le secret tant que la 2FA n'est pas confirmée."""
    tf, _ = TwoFactor.objects.get_or_create(user=user, defaults={"secret": totp.generate_secret()})
    if not tf.enabled:
        tf.secret = totp.generate_secret()
        tf.save(update_fields=["secret", "updated_at"])
    return tf


def enable(user, code: str) -> list[str] | None:
    """Active la 2FA si le code TOTP est valide. Renvoie les codes de secours."""
    tf = getattr(user, "two_factor", None)
    if tf is None or tf.enabled or not totp.verify(tf.secret, code):
        return None
    recovery = _generate_recovery_codes()
    tf.enabled = True
    tf.confirmed_at = timezone.now()
    tf.recovery_codes = [_hash_code(c) for c in recovery]
    tf.save(update_fields=["enabled", "confirmed_at", "recovery_codes", "updated_at"])
    return recovery


def verify(user, code: str) -> bool:
    """Vérifie un code TOTP ou un code de secours (consommé si utilisé)."""
    tf = getattr(user, "two_factor", None)
    if tf is None or not tf.enabled or not code:
        return False
    if totp.verify(tf.secret, code):
        return True
    hashed = _hash_code(code.strip())
    if hashed in tf.recovery_codes:
        tf.recovery_codes.remove(hashed)
        tf.save(update_fields=["recovery_codes", "updated_at"])
        return True
    return False


def disable(user, code: str) -> bool:
    """Désactive la 2FA si le code (TOTP ou secours) est valide."""
    if not verify(user, code):
        return False
    TwoFactor.objects.filter(user=user).delete()
    return True
