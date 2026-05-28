"""Endpoints chat : historique (public) + gestion des bans (streamer)."""

from __future__ import annotations

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from channels_app.models import Channel

from .models import ChatBan, ChatIpBan
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


def _my_channel(user) -> Channel:
    channel, _ = Channel.objects.get_or_create(user=user, defaults={"slug": user.username})
    return channel


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_chat_bans(request: Request) -> Response:
    """Bans actifs (utilisateurs + IP) sur la chaîne du streamer connecté."""
    channel = _my_channel(request.user)
    user_bans = [
        {
            "username": b.user.username,
            "display_name": b.user.display_name or b.user.username,
            "until": b.until,
            "shadow": b.shadow,
            "reason": b.reason,
        }
        for b in ChatBan.objects.filter(channel=channel).select_related("user")
        if b.is_active()
    ]
    ip_bans = [
        {"ip": b.ip, "until": b.until, "reason": b.reason}
        for b in ChatIpBan.objects.filter(channel=channel)
        if b.is_active()
    ]
    return Response({"user_bans": user_bans, "ip_bans": ip_bans})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def lift_user_ban(request: Request, username: str) -> Response:
    channel = _my_channel(request.user)
    ChatBan.objects.filter(channel=channel, user__username=username.lower()).delete()
    return Response(status=204)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def lift_ip_ban(request: Request, ip: str) -> Response:
    channel = _my_channel(request.user)
    ChatIpBan.objects.filter(channel=channel, ip=ip).delete()
    return Response(status=204)
