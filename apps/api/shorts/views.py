"""Endpoints « Instant » : fil public, lecture, vues, likes, gestion streamer."""

from __future__ import annotations

from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from . import services
from .models import Short, ShortLike
from .serializers import MyShortSerializer, ShortCreateSerializer, ShortSerializer


def _paginate(request: Request, default: int = 20) -> tuple[int, int]:
    try:
        limit = max(1, min(int(request.query_params.get("limit", default)), 50))
    except (TypeError, ValueError):
        limit = default
    try:
        offset = max(int(request.query_params.get("offset", 0)), 0)
    except (TypeError, ValueError):
        offset = 0
    return limit, offset


def _liked_ids(request: Request, shorts) -> set[int]:
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return set()
    return set(
        ShortLike.objects.filter(user=user, short__in=list(shorts)).values_list(
            "short_id", flat=True
        )
    )


def _visible_or_404(pk: int) -> Short | None:
    return services.visible_shorts().filter(pk=pk).first()


@api_view(["GET"])
@permission_classes([AllowAny])
def trending(request: Request) -> Response:
    """Fil « Instant » public : les vidéos les plus populaires, suivies ou non."""
    limit, offset = _paginate(request)
    shorts = services.trending(limit=limit, offset=offset)
    ctx = {"liked_ids": _liked_ids(request, shorts)}
    return Response(
        {
            "results": ShortSerializer(shorts, many=True, context=ctx).data,
            "next_offset": offset + len(shorts) if len(shorts) == limit else None,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def channel_shorts(request: Request, slug: str) -> Response:
    """Vidéos Instant d'une chaîne (les plus récentes)."""
    limit, offset = _paginate(request)
    shorts = list(
        services.visible_shorts()
        .filter(channel__slug=slug.lower())
        .order_by("-published_at")[offset : offset + limit]
    )
    ctx = {"liked_ids": _liked_ids(request, shorts)}
    return Response({"results": ShortSerializer(shorts, many=True, context=ctx).data})


@api_view(["GET"])
@permission_classes([AllowAny])
def detail(request: Request, pk: int) -> Response:
    short = _visible_or_404(pk)
    if short is None:
        return Response({"detail": "Vidéo introuvable."}, status=status.HTTP_404_NOT_FOUND)
    ctx = {"liked_ids": _liked_ids(request, [short])}
    return Response(ShortSerializer(short, context=ctx).data)


@api_view(["POST"])
@permission_classes([AllowAny])
@ratelimit(key="ip", rate="240/h", method="POST", block=True)
def view(request: Request, pk: int) -> Response:
    short = _visible_or_404(pk)
    if short is None:
        return Response({"detail": "Vidéo introuvable."}, status=status.HTTP_404_NOT_FOUND)
    user = request.user
    from config.client_ip import client_ip

    viewer = f"u{user.pk}" if user.is_authenticated else f"ip{client_ip(request)}"
    counted = services.register_view(short, viewer)
    return Response({"counted": counted})


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
@ratelimit(key="user", rate="300/h", block=True)
def like(request: Request, pk: int) -> Response:
    short = _visible_or_404(pk)
    if short is None:
        return Response({"detail": "Vidéo introuvable."}, status=status.HTTP_404_NOT_FOUND)
    if request.method == "POST":
        services.like(request.user, short)
    else:
        services.unlike(request.user, short)
    short.refresh_from_db(fields=["like_count"])
    return Response({"liked": request.method == "POST", "like_count": short.like_count})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def mine(request: Request) -> Response:
    """GET : mes vidéos Instant (tous statuts). POST : démarre un upload."""
    if request.method == "GET":
        shorts = Short.objects.filter(channel__user=request.user).order_by("-created_at")[:100]
        return Response({"results": MyShortSerializer(shorts, many=True).data})
    serializer = ShortCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        short, upload = services.create_upload(request.user, serializer.validated_data["title"])
    except services.ShortError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(
        {"short": MyShortSerializer(short).data, "upload": upload},
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mine_uploaded(request: Request, pk: int) -> Response:
    try:
        short = services.mark_uploaded(request.user, pk)
    except services.ShortError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
    return Response(MyShortSerializer(short).data)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def mine_delete(request: Request, pk: int) -> Response:
    try:
        services.delete_short(request.user, pk)
    except services.ShortError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_204_NO_CONTENT)
