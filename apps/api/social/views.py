"""Endpoints follow / unfollow / liste / statut."""

from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from channels_app.models import Channel
from channels_app.serializers import PublicChannelSerializer

from .models import Collaboration
from .services import (
    CollaborationError,
    FollowError,
    follow_user,
    invite_collaborator,
    is_following,
    remove_collaboration,
    respond_collaboration,
    unfollow_user,
)


def _collab_view(collab: Collaboration, me_id: int) -> dict:
    other = collab.invitee if collab.inviter_id == me_id else collab.inviter
    return {
        "id": collab.id,
        "status": collab.status,
        "direction": "outgoing" if collab.inviter_id == me_id else "incoming",
        "user": {
            "username": other.username,
            "display_name": other.display_name or other.username,
            "avatar_url": other.avatar_url,
        },
        "created_at": collab.created_at,
    }


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
    from chat.redis_store import bulk_viewers_count

    viewers_map = bulk_viewers_count([c.id for c in ordered])
    data = PublicChannelSerializer(ordered, many=True).data
    for channel, item in zip(ordered, data, strict=False):
        item["viewers"] = viewers_map.get(channel.id, 0)
    return Response({"results": data})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def collaborations(request: Request) -> Response:
    """GET : mes collaborations (entrantes/sortantes/actives). POST : inviter."""
    from django.db.models import Q

    if request.method == "POST":
        username = (request.data.get("username") or "").strip()
        try:
            collab = invite_collaborator(request.user, username)
        except CollaborationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(_collab_view(collab, request.user.id), status=status.HTTP_201_CREATED)

    qs = (
        Collaboration.objects.filter(Q(inviter=request.user) | Q(invitee=request.user))
        .select_related("inviter", "invitee")
        .exclude(status=Collaboration.Status.DECLINED)
    )
    active, incoming, outgoing = [], [], []
    for c in qs:
        view = _collab_view(c, request.user.id)
        if c.status == Collaboration.Status.ACCEPTED:
            active.append(view)
        elif view["direction"] == "incoming":
            incoming.append(view)
        else:
            outgoing.append(view)
    return Response({"active": active, "incoming": incoming, "outgoing": outgoing})


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def collaboration_detail(request: Request, pk: int) -> Response:
    if request.method == "DELETE":
        remove_collaboration(request.user, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)
    action = request.data.get("action")
    collab = respond_collaboration(request.user, pk, accept=action == "accept")
    if collab is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(_collab_view(collab, request.user.id))
