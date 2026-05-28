"""TOTP (RFC 6238) en pur stdlib — pas de dépendance externe.

Compatible Google Authenticator / Authy : SHA1, 6 chiffres, période 30 s.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

PERIOD = 30
DIGITS = 6


def generate_secret(length: int = 20) -> str:
    """Secret aléatoire encodé en base32 (sans padding)."""
    return base64.b32encode(secrets.token_bytes(length)).decode().rstrip("=")


def _hotp(secret: str, counter: int) -> str:
    # base32 attend un padding multiple de 8.
    padded = secret + "=" * (-len(secret) % 8)
    key = base64.b32decode(padded, casefold=True)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % (10**DIGITS)
    return str(code).zfill(DIGITS)


def verify(secret: str, code: str, window: int = 1, now: int | None = None) -> bool:
    """Vérifie un code sur une fenêtre ± `window` périodes (tolérance d'horloge)."""
    if not secret or not code:
        return False
    code = code.strip().replace(" ", "")
    if not code.isdigit():
        return False
    counter = int((now if now is not None else time.time()) // PERIOD)
    for drift in range(-window, window + 1):
        if hmac.compare_digest(_hotp(secret, counter + drift), code):
            return True
    return False


def provisioning_uri(secret: str, account_name: str, issuer: str = "Neyla TV") -> str:
    """URI otpauth:// à encoder en QR code côté client."""
    label = quote(f"{issuer}:{account_name}")
    params = (
        f"secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits={DIGITS}&period={PERIOD}"
    )
    return f"otpauth://totp/{label}?{params}"
