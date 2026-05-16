"""Endpoint historique : sert les derniers messages depuis Redis."""

from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from channels_app.models import Channel

from .redis_store import MAX_MESSAGES, get_history


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def chat_history(request: Request, slug: str) -> Response:
    channel = Channel.objects.filter(slug=slug.lower()).only("id").first()
    if channel is None:
        raise NotFound("Chaîne introuvable.")
    try:
        limit = min(int(request.query_params.get("limit", MAX_MESSAGES)), MAX_MESSAGES)
    except (TypeError, ValueError):
        limit = MAX_MESSAGES
    return Response({"messages": get_history(channel.id, limit=limit)})
