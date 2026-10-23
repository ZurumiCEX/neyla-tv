"""IP réelle du client derrière les proxys (Cloudflare, DigitalOcean App Platform).

Sans cela, `REMOTE_ADDR` vaut l'adresse du load balancer pour TOUS les
visiteurs : les limites de débit par IP (inscription, connexion…) se
déclenchent alors pour tout le site à la fois.

Ordre de confiance : `CF-Connecting-IP` (Cloudflare), `DO-Connecting-IP`
(App Platform), premier élément de `X-Forwarded-For`, puis `REMOTE_ADDR`.
Sert aussi de `RATELIMIT_IP_META_KEY` pour django-ratelimit.
"""

from __future__ import annotations

import ipaddress

_HEADERS = ("HTTP_CF_CONNECTING_IP", "HTTP_DO_CONNECTING_IP")


def _valid(value: str) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return None
    return value


def client_ip(request) -> str:
    meta = request.META
    for header in _HEADERS:
        ip = _valid(meta.get(header, ""))
        if ip:
            return ip
    forwarded = meta.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        ip = _valid(forwarded.split(",")[0])
        if ip:
            return ip
    return meta.get("REMOTE_ADDR", "") or ""
