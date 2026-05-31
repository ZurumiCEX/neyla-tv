"""Validation de captcha Cloudflare Turnstile (gratuit, fonctionne en Afrique).

- Si `TURNSTILE_SECRET_KEY` est vide, le mode FAKE accepte tout token non vide
  (utilisable en dev/test sans appel réseau).
- En prod, appel `siteverify` (3s max) avec l'IP du client.
- Sert aussi de mécanisme d'amplification : on n'exige un token que sur les
  endpoints sensibles (`register`, `login` après N échecs).
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

from django.conf import settings

_ENDPOINT = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def is_enabled() -> bool:
    return bool(getattr(settings, "TURNSTILE_SECRET_KEY", "") or "")


def verify(token: str, client_ip: str = "") -> bool:
    """Valide un token Turnstile. En mode FAKE (pas de clé), accepte tout non vide."""
    token = (token or "").strip()
    if not token:
        return False
    secret = getattr(settings, "TURNSTILE_SECRET_KEY", "") or ""
    if not secret:
        return True  # FAKE : pas de clé → on ne bloque pas le dev/tests.
    try:
        data = urllib.parse.urlencode(
            {"secret": secret, "response": token, "remoteip": client_ip or ""}
        ).encode()
        req = urllib.request.Request(  # noqa: S310 - URL https fixe (Cloudflare)
            _ENDPOINT, data=data, method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as r:  # noqa: S310 - URL https fixe
            payload = json.loads(r.read().decode("utf-8") or "{}")
        return bool(payload.get("success"))
    except Exception:
        return False


# Domaines email jetables courants — bloque l'inscription.
DISPOSABLE_EMAIL_DOMAINS: frozenset[str] = frozenset(
    {
        "yopmail.com",
        "mailinator.com",
        "guerrillamail.com",
        "tempmail.com",
        "10minutemail.com",
        "trashmail.com",
        "throwawaymail.com",
        "fakeinbox.com",
        "dispostable.com",
        "getairmail.com",
        "moakt.com",
        "sharklasers.com",
        "maildrop.cc",
        "harakirimail.com",
        "0wnd.org",
    }
)


def is_disposable(email: str) -> bool:
    domain = (email or "").rsplit("@", 1)[-1].lower().strip()
    return domain in DISPOSABLE_EMAIL_DOMAINS
