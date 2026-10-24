"""Chiffrement des secrets au repos (secret TOTP) et hachage des codes de secours.

Clé : FIELD_ENCRYPTION_KEY (clé Fernet) si fournie, sinon dérivée de SECRET_KEY.
Les valeurs chiffrées sont préfixées « enc: » ; une valeur sans préfixe est
considérée comme en clair (données antérieures) et reste lisible.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

from django.conf import settings

PREFIX = "enc:"


def _fernet():
    from cryptography.fernet import Fernet

    key = getattr(settings, "FIELD_ENCRYPTION_KEY", "") or ""
    if not key:
        digest = hashlib.sha256(f"neyla-field-key:{settings.SECRET_KEY}".encode()).digest()
        key = base64.urlsafe_b64encode(digest).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(value: str) -> str:
    if not value or value.startswith(PREFIX):
        return value
    return PREFIX + _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    if not value or not value.startswith(PREFIX):
        return value
    return _fernet().decrypt(value[len(PREFIX) :].encode()).decode()


def hash_code(code: str) -> str:
    """HMAC des codes de secours (clé serveur) : inexploitable sans la clé."""
    digest = hmac.new(settings.SECRET_KEY.encode(), code.encode(), hashlib.sha256).hexdigest()
    return f"h1:{digest}"


def legacy_hash(code: str) -> str:
    """Ancien format (SHA-256 simple), encore accepté pour les codes existants."""
    return hashlib.sha256(code.encode()).hexdigest()
