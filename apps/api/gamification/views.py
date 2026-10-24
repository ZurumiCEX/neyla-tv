"""Endpoint : catalogue des succès + ceux débloqués par l'utilisateur courant."""

from __future__ import annotations

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from . import services
from .models import Achievement, UserAchievement
from .serializers import AchievementSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_achievements(request: Request) -> Response:
    services.sync_catalog()
    unlocked_map = {
        ua.achievement.key: ua.awarded_at
        for ua in UserAchievement.objects.select_related("achievement").filter(user=request.user)
    }
    achievements = Achievement.objects.filter(is_active=True)
    data = AchievementSerializer(
        achievements, many=True, context={"unlocked_map": unlocked_map}
    ).data
    return Response({"results": data, "unlocked": len(unlocked_map), "total": len(data)})


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def user_achievements(request: Request, username: str) -> Response:
    """Succès DÉBLOQUÉS d'un utilisateur (public) : profil + pastille avatar."""
    from accounts.models import User

    user = User.objects.filter(username=username.lower()).first()
    if user is None:
        return Response({"results": [], "unlocked": 0})
    qs = (
        UserAchievement.objects.select_related("achievement")
        .filter(user=user, achievement__is_active=True)
        .order_by("achievement__order", "achievement__id")
    )
    unlocked_map = {ua.achievement.key: ua.awarded_at for ua in qs}
    achievements = [ua.achievement for ua in qs]
    data = AchievementSerializer(
        achievements, many=True, context={"unlocked_map": unlocked_map}
    ).data
    return Response({"results": data, "unlocked": len(data)})


def _level_payload(spent: int, owner: bool) -> dict:
    from .levels import level_progress

    data = level_progress(spent)
    if owner:
        data["spent"] = spent
    return data


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_level(request: Request) -> Response:
    """Niveau et progression de l'utilisateur connecté (portefeuille, header)."""
    request.user.refresh_from_db(fields=["lifetime_aura_spent"])
    return Response(_level_payload(request.user.lifetime_aura_spent, owner=True))


@api_view(["GET"])
@permission_classes([AllowAny])
def public_profile(request: Request, username: str) -> Response:
    """Profil public : niveau, badges de don par chaîne, succès, chiffres clés.

    Les montants exacts ne sont visibles que par le propriétaire du profil.
    """
    from accounts.models import User
    from channels_app.models import Channel
    from social.models import Follow

    from .levels import gift_tier
    from .models import ChannelSupport

    user = User.objects.filter(username=username.lower(), is_active=True).first()
    if user is None:
        return Response({"detail": "Profil introuvable."}, status=404)
    viewer = getattr(request, "user", None)
    owner = bool(viewer and viewer.is_authenticated and viewer.pk == user.pk)

    services.sync_catalog()
    unlocked_map = {
        ua.achievement.key: ua.awarded_at
        for ua in UserAchievement.objects.select_related("achievement").filter(
            user=user, achievement__is_active=True
        )
    }
    catalog = Achievement.objects.filter(is_active=True)
    if not owner:
        catalog = catalog.filter(key__in=unlocked_map.keys())
    achievements = AchievementSerializer(
        catalog, many=True, context={"unlocked_map": unlocked_map}
    ).data

    supports = (
        ChannelSupport.objects.filter(user=user, total_aura__gt=0)
        .select_related("channel__user")
        .order_by("-total_aura")[:6]
    )
    supported = []
    for s in supports:
        item = {
            "slug": s.channel.slug,
            "display_name": s.channel.user.display_name or s.channel.user.username,
            "avatar_url": s.channel.user.avatar_url,
            "gift_tier": gift_tier(s.total_aura),
        }
        if owner:
            item["total_aura"] = s.total_aura
        supported.append(item)

    channel = Channel.objects.filter(user=user).first()
    return Response(
        {
            "username": user.username,
            "display_name": user.display_name or user.username,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
            "joined_at": user.date_joined,
            "is_owner": owner,
            "channel": (
                {"slug": channel.slug, "is_live": channel.is_live}
                if channel is not None and channel.is_provisioned
                else None
            ),
            "level": _level_payload(user.lifetime_aura_spent, owner),
            "supported": supported,
            "achievements": achievements,
            "achievements_unlocked": len(unlocked_map),
            "following_count": Follow.objects.filter(follower=user).count(),
            "follower_count": Follow.objects.filter(followee=user).count(),
        }
    )
