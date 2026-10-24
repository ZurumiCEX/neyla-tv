"""Contrôle de l'origine des connexions WebSocket (anti-CSWSH).

Origines acceptées : hôtes de ALLOWED_HOSTS, origines CORS (liste exacte et
expressions régulières, ex. previews Vercel). En DEBUG, tout est accepté.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from channels.security.websocket import WebsocketDenier
from django.conf import settings
from django.http.request import validate_host


def origin_allowed(origin: str) -> bool:
    if settings.DEBUG:
        return True
    if not origin:
        # Pas d'Origin = client non navigateur (OBS, scripts) : pas de risque CSWSH,
        # qui exige un navigateur (lequel envoie toujours l'en-tête).
        return True
    if origin in getattr(settings, "CORS_ALLOWED_ORIGINS", []):
        return True
    if any(re.match(p, origin) for p in getattr(settings, "CORS_ALLOWED_ORIGIN_REGEXES", [])):
        return True
    host = urlparse(origin).hostname or ""
    return validate_host(host, settings.ALLOWED_HOSTS)


class OriginValidator:
    def __init__(self, application):
        self.application = application

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            origin = ""
            for name, value in scope.get("headers", []):
                if name == b"origin":
                    origin = value.decode("latin1")
                    break
            if not origin_allowed(origin):
                return await WebsocketDenier()(scope, receive, send)
        return await self.application(scope, receive, send)
