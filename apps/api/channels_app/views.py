"""Endpoints REST pour les chaînes."""

from __future__ import annotations

from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Channel
from .serializers import (
    MyChannelSerializer,
    PublicChannelSerializer,
    StreamSessionSerializer,
)
from .services import rotate_stream_key


def _get_my_channel(user) -> Channel:
    """Récupère la chaîne de l'utilisateur (créée à l'inscription, non provisionnée).

    Le provisioning n'a lieu qu'à l'approbation streamer — pas ici.
    """
    channel, _ = Channel.objects.get_or_create(user=user, defaults={"slug": user.username})
    return channel


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def my_channel(request: Request) -> Response:
    channel = _get_my_channel(request.user)
    if request.method == "GET":
        from chat.redis_store import get_viewers_count
        from social.models import Follow

        data = MyChannelSerializer(channel).data
        data["follower_count"] = Follow.objects.filter(followee=request.user).count()
        data["viewers"] = get_viewers_count(channel.id)
        return Response(data)
    serializer = MyChannelSerializer(channel, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_sessions(request: Request) -> Response:
    """Historique des sessions de diffusion du propriétaire (les plus récentes)."""
    channel = _get_my_channel(request.user)
    try:
        limit = min(int(request.query_params.get("limit", 50)), 100)
    except (TypeError, ValueError):
        limit = 50
    sessions = channel.sessions.all()[:limit]
    return Response({"results": StreamSessionSerializer(sessions, many=True).data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="5/d", method="POST", block=True)
def rotate_key(request: Request) -> Response:  # noqa: ARG001
    channel = _get_my_channel(request.user)
    if not channel.is_provisioned:
        raise PermissionDenied(
            "Chaîne non provisionnée : l'accès streamer doit d'abord être approuvé."
        )
    rotate_stream_key(channel)
    channel.refresh_from_db()
    return Response(MyChannelSerializer(channel).data)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def public_channel(request: Request, slug: str) -> Response:  # noqa: ARG001
    channel = Channel.objects.select_related("user").filter(slug=slug.lower()).first()
    if channel is None:
        raise NotFound("Chaîne introuvable.")
    return Response(PublicChannelSerializer(channel).data, status=status.HTTP_200_OK)


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def channel_status(request: Request, slug: str) -> Response:  # noqa: ARG001
    """Payload léger pour le badge LIVE + viewers (poll 5s, cacheable côté CDN)."""
    channel = (
        Channel.objects.filter(slug=slug.lower())
        .only("id", "is_live", "last_live_started_at")
        .first()
    )
    if channel is None:
        raise NotFound("Chaîne introuvable.")
    from chat.redis_store import get_viewers_count

    response = Response(
        {
            "is_live": channel.is_live,
            "last_live_started_at": channel.last_live_started_at,
            "viewers": get_viewers_count(channel.id),
        }
    )
    response["Cache-Control"] = "public, max-age=5"
    return response
