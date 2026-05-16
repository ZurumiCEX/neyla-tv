"""Endpoints REST pour les chaînes."""

from __future__ import annotations

from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Channel
from .serializers import MyChannelSerializer, PublicChannelSerializer
from .services import provision_channel, rotate_stream_key


def _get_or_provision_my_channel(user) -> Channel:
    channel, _ = Channel.objects.get_or_create(user=user, defaults={"slug": user.username})
    if not channel.is_provisioned:
        provision_channel(channel)
    return channel


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def my_channel(request: Request) -> Response:
    channel = _get_or_provision_my_channel(request.user)
    if request.method == "GET":
        return Response(MyChannelSerializer(channel).data)
    serializer = MyChannelSerializer(channel, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="5/d", method="POST", block=True)
def rotate_key(request: Request) -> Response:  # noqa: ARG001
    channel = _get_or_provision_my_channel(request.user)
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
    """Payload léger pour le badge LIVE (poll 5s, cacheable côté CDN)."""
    channel = (
        Channel.objects.filter(slug=slug.lower()).only("is_live", "last_live_started_at").first()
    )
    if channel is None:
        raise NotFound("Chaîne introuvable.")
    response = Response(
        {
            "is_live": channel.is_live,
            "last_live_started_at": channel.last_live_started_at,
        }
    )
    response["Cache-Control"] = "public, max-age=5"
    return response
