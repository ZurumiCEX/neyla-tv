"""Endpoints découverte : lives en cours, catégories, recherche."""

from __future__ import annotations

from django.db.models import Count, Q
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from channels_app.models import Channel
from channels_app.serializers import PublicChannelSerializer
from chat.redis_store import bulk_viewers_count

from .models import Game
from .serializers import GameSerializer, GameWithCountSerializer

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def _paginate(request: Request) -> tuple[int, int]:
    try:
        limit = min(int(request.query_params.get("limit", DEFAULT_LIMIT)), MAX_LIMIT)
    except (TypeError, ValueError):
        limit = DEFAULT_LIMIT
    try:
        offset = max(int(request.query_params.get("offset", 0)), 0)
    except (TypeError, ValueError):
        offset = 0
    return limit, offset


def _viewers_for(channel_ids: list[int]) -> dict[int, int]:
    """Compteur de spectateurs par chaîne, avec repli prod-safe.

    Source primaire : présence temps réel (Redis). Si la carte est entièrement
    vide (Redis indisponible, démarrage à froid, ou données de seed sans Redis),
    on estime via le pic de la session en cours. Le repli ne se déclenche que
    lorsque AUCUNE chaîne n'a de présence (donc le comportement prod normal,
    où au moins une chaîne a des spectateurs, est inchangé).
    """
    if not channel_ids:
        return {}
    viewers_map = bulk_viewers_count(channel_ids)
    if any(viewers_map.values()):
        return viewers_map
    from channels_app.models import StreamSession

    peaks: dict[int, int] = {}
    for cid, peak in (
        StreamSession.objects.filter(channel_id__in=channel_ids, ended_at__isnull=True)
        .values_list("channel_id", "peak_viewers")
        .order_by("channel_id")
    ):
        peaks[cid] = max(peaks.get(cid, 0), int(peak or 0))
    return {cid: peaks.get(cid, 0) for cid in channel_ids}


def _serialize_live_with_viewers(channels: list[Channel]) -> list[dict]:
    viewers_map = _viewers_for([c.id for c in channels])
    sorted_channels = sorted(channels, key=lambda c: viewers_map.get(c.id, 0), reverse=True)
    data = PublicChannelSerializer(sorted_channels, many=True).data
    for item, channel in zip(data, sorted_channels, strict=True):
        item["viewers"] = viewers_map.get(channel.id, 0)
    return data


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def discover_live(request: Request) -> Response:
    limit, offset = _paginate(request)
    qs = Channel.objects.filter(is_live=True).select_related("user", "category")
    channels = list(qs)
    serialized = _serialize_live_with_viewers(channels)
    paginated = serialized[offset : offset + limit]
    return Response({"results": paginated, "total": len(serialized)})


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def discover_categories(request: Request) -> Response:
    limit, offset = _paginate(request)
    qs = Game.objects.annotate(
        live_count=Count("channels", filter=Q(channels__is_live=True))
    )
    group = (request.query_params.get("group") or "").strip().lower()
    if group in dict(Game.Group.choices):
        qs = qs.filter(group=group)
    games = list(qs.order_by("-live_count", "name")[offset : offset + limit])
    data = GameWithCountSerializer(games, many=True).data
    # Total spectateurs par catégorie (somme des viewers des lives, repli pic).
    live = list(
        Channel.objects.filter(is_live=True, category__in=games).values_list("id", "category_id")
    )
    viewers_map = _viewers_for([cid for cid, _ in live])
    totals: dict[int, int] = {}
    for channel_id, category_id in live:
        totals[category_id] = totals.get(category_id, 0) + viewers_map.get(channel_id, 0)
    for item, game in zip(data, games, strict=True):
        item["viewers"] = totals.get(game.id, 0)
    return Response({"results": data})


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def discover_groups(request: Request) -> Response:
    """Macro-catégories style Twitch (Jeux, IRL, Discussions, Musique, Créativité).

    Pour chaque groupe : nombre de catégories et de lives en cours.
    """
    counts = {g: 0 for g, _ in Game.Group.choices}
    lives = {g: 0 for g, _ in Game.Group.choices}
    for group, count in (
        Game.objects.values_list("group").annotate(n=Count("id")).values_list("group", "n")
    ):
        counts[group] = count
    for group, count in (
        Channel.objects.filter(is_live=True, category__isnull=False)
        .values_list("category__group")
        .annotate(n=Count("id"))
        .values_list("category__group", "n")
    ):
        lives[group] = count
    return Response(
        {
            "results": [
                {
                    "slug": g,
                    "name": label,
                    "category_count": counts[g],
                    "live_count": lives[g],
                }
                for g, label in Game.Group.choices
            ]
        }
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def discover_category(request: Request, slug: str) -> Response:
    game = Game.objects.filter(slug=slug.lower()).first()
    if game is None:
        raise NotFound("Catégorie introuvable.")
    limit, offset = _paginate(request)
    channels = list(
        Channel.objects.filter(is_live=True, category=game).select_related("user", "category")
    )
    serialized = _serialize_live_with_viewers(channels)
    return Response(
        {
            "category": GameSerializer(game).data,
            "results": serialized[offset : offset + limit],
            "total": len(serialized),
        }
    )


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def discover_search(request: Request) -> Response:
    q = (request.query_params.get("q") or "").strip()
    if len(q) < 2:
        return Response({"channels": [], "games": []})
    channels = (
        Channel.objects.select_related("user", "category")
        .filter(
            Q(slug__icontains=q)
            | Q(user__display_name__icontains=q)
            | Q(tags__contains=[q.lower()])
        )
        .order_by("-is_live", "slug")[:20]
    )
    games = Game.objects.filter(name__icontains=q).order_by("name")[:20]
    return Response(
        {
            "channels": PublicChannelSerializer(channels, many=True).data,
            "games": GameSerializer(games, many=True).data,
        }
    )
