"""Middleware Channels qui résout l'utilisateur via JWT en query param."""

from __future__ import annotations

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _user_from_token(token: str | None):
    if not token:
        return AnonymousUser()
    try:
        from rest_framework_simplejwt.authentication import JWTAuthentication
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

        auth = JWTAuthentication()
        validated = auth.get_validated_token(token)
        return auth.get_user(validated)
    except (InvalidToken, TokenError, Exception):
        return AnonymousUser()


class TokenAuthMiddleware:
    """Lit `?token=<jwt>` sur le scope WebSocket et pose `scope["user"]`."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        qs = parse_qs(scope.get("query_string", b"").decode())
        token = (qs.get("token") or [None])[0]
        scope["user"] = await _user_from_token(token)
        return await self.inner(scope, receive, send)
