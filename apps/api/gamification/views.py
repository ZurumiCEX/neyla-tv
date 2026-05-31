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
        .filter(user=user)
        .order_by("achievement__order", "achievement__id")
    )
    unlocked_map = {ua.achievement.key: ua.awarded_at for ua in qs}
    achievements = [ua.achievement for ua in qs]
    data = AchievementSerializer(
        achievements, many=True, context={"unlocked_map": unlocked_map}
    ).data
    return Response({"results": data, "unlocked": len(data)})
