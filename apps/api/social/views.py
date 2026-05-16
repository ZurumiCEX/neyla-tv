"""Endpoints follow / unfollow / liste / statut."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from channels_app.models import Channel
from channels_app.serializers import PublicChannelSerializer

from .services import FollowError, follow_user, is_following, unfollow_user


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def follow_endpoint(request: Request, username: str) -> Response:
    try:
        if request.method == "POST":
            follow_user(request.user, username)
            return Response({"following": True}, status=status.HTTP_201_CREATED)
        unfollow_user(request.user, username)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except FollowError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def follow_status(request: Request, username: str) -> Response:
    return Response({"following": is_following(request.user, username)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_followings(request: Request) -> Response:
    """Liste les chaînes que je suis (ordonnées par date follow desc)."""
    followee_ids = list(
        request.user.following.order_by("-created_at").values_list("followee_id", flat=True)
    )
    if not followee_ids:
        return Response({"results": []})
    channels = Channel.objects.select_related("user", "category").filter(user_id__in=followee_ids)
    # Préserve l'ordre des follows (la requête DB ne le garantit pas).
    by_user = {c.user_id: c for c in channels}
    ordered = [by_user[uid] for uid in followee_ids if uid in by_user]
    return Response({"results": PublicChannelSerializer(ordered, many=True).data})
