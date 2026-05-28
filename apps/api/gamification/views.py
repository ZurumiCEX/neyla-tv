"""Endpoint : catalogue des succès + ceux débloqués par l'utilisateur courant."""

from __future__ import annotations

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
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
    achievements = Achievement.objects.all()
    data = AchievementSerializer(
        achievements, many=True, context={"unlocked_map": unlocked_map}
    ).data
    return Response({"results": data, "unlocked": len(unlocked_map), "total": len(data)})
