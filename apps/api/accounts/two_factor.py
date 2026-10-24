"""Logique métier 2FA : setup, activation, codes de secours, vérification.

- Secret TOTP chiffré au repos (accounts.crypto).
- Anti-rejeu : un code TOTP déjà accepté (même période) est refusé.
- Codes de secours hachés (HMAC), consommés sous verrou de ligne.
"""

from __future__ import annotations

import secrets

from django.db import transaction
from django.utils import timezone

from . import totp
from .crypto import decrypt, encrypt, hash_code, legacy_hash
from .models import TwoFactor

RECOVERY_CODE_COUNT = 10


def _generate_recovery_codes() -> list[str]:
    codes = []
    for _ in range(RECOVERY_CODE_COUNT):
        raw = secrets.token_hex(5)
        codes.append(f"{raw[:5]}-{raw[5:]}")
    return codes


def is_enabled(user) -> bool:
    tf = getattr(user, "two_factor", None)
    return bool(tf and tf.enabled)


def plain_secret(tf: TwoFactor) -> str:
    return decrypt(tf.secret)


def begin_setup(user) -> tuple[TwoFactor, str]:
    """Crée/rafraîchit le secret tant que la 2FA n'est pas confirmée. Renvoie (tf, secret)."""
    secret = totp.generate_secret()
    tf, created = TwoFactor.objects.get_or_create(user=user, defaults={"secret": encrypt(secret)})
    if not created and not tf.enabled:
        tf.secret = encrypt(secret)
        tf.last_used_step = None
        tf.save(update_fields=["secret", "last_used_step", "updated_at"])
    elif not created:
        secret = plain_secret(tf)
    return tf, secret


def enable(user, code: str) -> list[str] | None:
    """Active la 2FA si le code TOTP est valide. Renvoie les codes de secours."""
    with transaction.atomic():
        tf = TwoFactor.objects.select_for_update().filter(user=user).first()
        if tf is None or tf.enabled:
            return None
        step = totp.match_step(plain_secret(tf), code)
        if step is None:
            return None
        recovery = _generate_recovery_codes()
        tf.enabled = True
        tf.confirmed_at = timezone.now()
        tf.last_used_step = step
        tf.recovery_codes = [hash_code(c) for c in recovery]
        tf.save(
            update_fields=[
                "enabled",
                "confirmed_at",
                "last_used_step",
                "recovery_codes",
                "updated_at",
            ]
        )
    return recovery


def verify(user, code: str) -> bool:
    """Vérifie un code TOTP (non rejoué) ou un code de secours (consommé)."""
    code = (code or "").strip()
    if not code:
        return False
    with transaction.atomic():
        tf = TwoFactor.objects.select_for_update().filter(user=user, enabled=True).first()
        if tf is None:
            return False
        step = totp.match_step(plain_secret(tf), code)
        if step is not None:
            if tf.last_used_step is not None and step <= tf.last_used_step:
                return False  # code déjà utilisé (rejeu)
            tf.last_used_step = step
            tf.save(update_fields=["last_used_step", "updated_at"])
            return True
        for candidate in (hash_code(code.lower()), legacy_hash(code)):
            if candidate in tf.recovery_codes:
                tf.recovery_codes = [c for c in tf.recovery_codes if c != candidate]
                tf.save(update_fields=["recovery_codes", "updated_at"])
                return True
    return False


def regenerate_recovery_codes(user) -> list[str] | None:
    with transaction.atomic():
        tf = TwoFactor.objects.select_for_update().filter(user=user, enabled=True).first()
        if tf is None:
            return None
        codes = _generate_recovery_codes()
        tf.recovery_codes = [hash_code(c) for c in codes]
        tf.save(update_fields=["recovery_codes", "updated_at"])
    return codes


def remaining_recovery_codes(user) -> int:
    tf = getattr(user, "two_factor", None)
    return len(tf.recovery_codes) if tf and tf.enabled else 0


def disable(user, code: str) -> bool:
    """Désactive la 2FA si le code (TOTP ou secours) est valide."""
    if not verify(user, code):
        return False
    TwoFactor.objects.filter(user=user).delete()
    return True
