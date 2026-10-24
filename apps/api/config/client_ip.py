"""IP réelle du client derrière les proxys (Cloudflare, DigitalOcean App Platform).

Sans cela, `REMOTE_ADDR` vaut l'adresse du load balancer pour TOUS les
visiteurs : les limites de débit par IP (inscription, connexion…) se
déclenchent alors pour tout le site à la fois.

Ordre de confiance : `CF-Connecting-IP` (Cloudflare), `Fly-Client-IP`
(Fly.io), `DO-Connecting-IP` (App Platform), premier élément de
`X-Forwarded-For`, puis `REMOTE_ADDR`.
Sert aussi de `RATELIMIT_IP_META_KEY` pour django-ratelimit.
"""

from __future__ import annotations

import ipaddress

_HEADERS = ("cf-connecting-ip", "fly-client-ip", "do-connecting-ip")


def _valid(value: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return None
    return value


def ip_from_headers(get, remote: str | None) -> str:
    """IP client à partir d'un accès aux en-têtes (`get("x-forwarded-for")`).

    Si CLIENT_IP_HEADER est défini (ex. « Fly-Client-IP »), SEUL cet en-tête posé
    par le proxy est cru : impossible de falsifier son IP via X-Forwarded-For.
    """
    from django.conf import settings

    trusted = (getattr(settings, "CLIENT_IP_HEADER", "") or "").strip().lower()
    if trusted:
        return _valid(get(trusted)) or (remote or "")
    for header in _HEADERS:
        ip = _valid(get(header))
        if ip:
            return ip
    forwarded = get("x-forwarded-for")
    if forwarded:
        ip = _valid(forwarded.split(",")[0])
        if ip:
            return ip
    return remote or ""


def client_ip(request) -> str:
    meta = request.META
    return ip_from_headers(
        lambda name: meta.get("HTTP_" + name.upper().replace("-", "_"), ""),
        meta.get("REMOTE_ADDR", ""),
    )


def client_ip_from_scope(scope) -> str | None:
    """Même règle pour une connexion WebSocket (scope ASGI)."""
    headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
    client = scope.get("client")
    return (
        ip_from_headers(lambda name: headers.get(name, ""), client[0] if client else None) or None
    )
