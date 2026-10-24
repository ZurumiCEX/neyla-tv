"""Passkeys (WebAuthn) : enregistrement et connexion sans mot de passe.

Les défis (challenges) sont stockés 5 min dans le cache partagé (Redis) et
consommés une seule fois. L'origine attendue est le domaine du front
(WEBAUTHN_ORIGINS) et l'identifiant de RP son nom de domaine (WEBAUTHN_RP_ID).
"""

from __future__ import annotations

import json
import secrets

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from .models import Passkey

CHALLENGE_TTL = 300
MAX_PASSKEYS = 10


class PasskeyError(Exception):
    """Vérification WebAuthn refusée (défi expiré, signature invalide…)."""


def _rp() -> tuple[str, list[str]]:
    return settings.WEBAUTHN_RP_ID, list(settings.WEBAUTHN_ORIGINS)


def _pop(key: str) -> bytes | None:
    value = cache.get(key)
    if value is None:
        return None
    cache.delete(key)
    return base64url_to_bytes(value)


def registration_options(user) -> dict:
    rp_id, _ = _rp()
    options = generate_registration_options(
        rp_id=rp_id,
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_id=str(user.pk).encode(),
        user_name=user.email,
        user_display_name=user.display_name or user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(p.credential_id))
            for p in Passkey.objects.filter(user=user)
        ],
    )
    cache.set(f"webauthn:reg:{user.pk}", bytes_to_base64url(options.challenge), CHALLENGE_TTL)
    return json.loads(options_to_json(options))


def register(user, credential: dict, name: str) -> Passkey:
    if Passkey.objects.filter(user=user).count() >= MAX_PASSKEYS:
        raise PasskeyError(f"Limite de {MAX_PASSKEYS} passkeys atteinte.")
    challenge = _pop(f"webauthn:reg:{user.pk}")
    if challenge is None:
        raise PasskeyError("Délai dépassé, recommence l'ajout de la passkey.")
    rp_id, origins = _rp()
    try:
        verified = verify_registration_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=rp_id,
            expected_origin=origins,
        )
    except Exception as exc:  # noqa: BLE001 - erreurs variées de la lib (format, signature)
        raise PasskeyError("Passkey refusée par la vérification.") from exc
    transports = (credential.get("response") or {}).get("transports") or []
    return Passkey.objects.create(
        user=user,
        credential_id=bytes_to_base64url(verified.credential_id),
        public_key=bytes_to_base64url(verified.credential_public_key),
        sign_count=verified.sign_count,
        transports=[t for t in transports if isinstance(t, str)][:6],
        name=(name or "Passkey").strip()[:60] or "Passkey",
    )


def authentication_options() -> dict:
    """Options de connexion (passkeys « découvrables » : aucun identifiant demandé)."""
    rp_id, _ = _rp()
    options = generate_authentication_options(
        rp_id=rp_id, user_verification=UserVerificationRequirement.PREFERRED
    )
    handle = secrets.token_urlsafe(24)
    cache.set(f"webauthn:auth:{handle}", bytes_to_base64url(options.challenge), CHALLENGE_TTL)
    return {"handle": handle, "options": json.loads(options_to_json(options))}


def authenticate(handle: str, credential: dict):
    """Vérifie l'assertion et renvoie l'utilisateur (actif) propriétaire de la passkey."""
    challenge = _pop(f"webauthn:auth:{handle or ''}")
    if challenge is None:
        raise PasskeyError("Délai dépassé, réessaie.")
    passkey = (
        Passkey.objects.select_related("user")
        .filter(credential_id=credential.get("id", ""))
        .first()
    )
    if passkey is None or not passkey.user.is_active:
        raise PasskeyError("Passkey inconnue.")
    rp_id, origins = _rp()
    try:
        verified = verify_authentication_response(
            credential=credential,
            expected_challenge=challenge,
            expected_rp_id=rp_id,
            expected_origin=origins,
            credential_public_key=base64url_to_bytes(passkey.public_key),
            credential_current_sign_count=passkey.sign_count,
        )
    except Exception as exc:  # noqa: BLE001
        raise PasskeyError("Passkey refusée par la vérification.") from exc
    passkey.sign_count = verified.new_sign_count
    passkey.last_used_at = timezone.now()
    passkey.save(update_fields=["sign_count", "last_used_at"])
    return passkey.user
