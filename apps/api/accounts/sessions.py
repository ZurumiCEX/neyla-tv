"""Suivi des sessions d'appareil (adossé aux refresh tokens simplejwt).

Toutes les fonctions sont best-effort : une erreur ici ne doit jamais casser
le flux d'authentification.
"""

from __future__ import annotations

import contextlib
import logging

logger = logging.getLogger(__name__)


def _client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR") or None


def _device(request) -> str:
    return (request.META.get("HTTP_USER_AGENT") or "")[:300]


def record_login(user, request, refresh) -> None:
    """Crée (ou rafraîchit) la session de l'appareil au login."""
    with contextlib.suppress(Exception):
        from .models import UserSession

        jti = refresh.get("jti")
        if not jti:
            return
        UserSession.objects.update_or_create(
            jti=jti,
            defaults={
                "user": user,
                "device": _device(request),
                "ip": _client_ip(request),
                "revoked": False,
            },
        )


def record_rotation(old_jti, new_refresh, request) -> None:
    """Suit la rotation : la session conserve son identité, le jti est mis à jour."""
    with contextlib.suppress(Exception):
        from .models import UserSession

        new_jti = new_refresh.get("jti")
        if not new_jti:
            return
        session = UserSession.objects.filter(jti=old_jti).first()
        if session is not None:
            session.jti = new_jti
            session.ip = _client_ip(request) or session.ip
            if not session.device:
                session.device = _device(request)
            session.save(update_fields=["jti", "ip", "device", "last_seen_at"])


def revoke_jti(jti) -> None:
    """Marque la session révoquée et blackliste le refresh token correspondant."""
    with contextlib.suppress(Exception):
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
            OutstandingToken,
        )

        from .models import UserSession

        UserSession.objects.filter(jti=jti).update(revoked=True)
        outstanding = OutstandingToken.objects.filter(jti=jti).first()
        if outstanding is not None:
            BlacklistedToken.objects.get_or_create(token=outstanding)


def current_jti(request) -> str | None:
    """Récupère le jti du refresh token courant depuis le cookie (sans le révoquer)."""
    from django.conf import settings
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.tokens import RefreshToken

    token = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
    if not token:
        return None
    try:
        return RefreshToken(token).get("jti")
    except TokenError:
        return None
