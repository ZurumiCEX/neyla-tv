"""Analytics calculées À LA DEMANDE (pas de tâche nocturne / worker requis).

DAU/MAU s'appuient sur User.last_active_at (mis à jour à l'appel de /api/auth/me).
Le watch-time est approximé par les heures diffusées (durée des sessions).
"""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Max
from django.utils import timezone

from channels_app.models import Channel, StreamSession
from social.models import Follow

User = get_user_model()


def _broadcast_hours(qs) -> float:
    total = 0.0
    for session in qs.filter(ended_at__isnull=False).only("started_at", "ended_at"):
        total += (session.ended_at - session.started_at).total_seconds()
    return round(total / 3600, 1)


def platform_overview() -> dict:
    now = timezone.now()
    sessions = StreamSession.objects.all()
    top = (
        Channel.objects.select_related("user")
        .annotate(followers=Count("user__followers", distinct=True))
        .order_by("-followers")[:10]
    )
    return {
        "users_total": User.objects.count(),
        "dau": User.objects.filter(last_active_at__gte=now - timedelta(days=1)).count(),
        "mau": User.objects.filter(last_active_at__gte=now - timedelta(days=30)).count(),
        "streamers_total": Channel.objects.exclude(live_input_uid="").count(),
        "live_now": Channel.objects.filter(is_live=True).count(),
        "streams_total": sessions.count(),
        "streams_7d": sessions.filter(started_at__gte=now - timedelta(days=7)).count(),
        "broadcast_hours": _broadcast_hours(sessions),
        "peak_concurrent": sessions.aggregate(m=Max("peak_viewers"))["m"] or 0,
        "top_streamers": [
            {"username": c.user.username, "followers": c.followers, "is_live": c.is_live}
            for c in top
        ],
    }


def my_analytics(user) -> dict:
    sessions = StreamSession.objects.filter(channel__user=user)
    return {
        "sessions_total": sessions.count(),
        "broadcast_hours": _broadcast_hours(sessions),
        "peak_viewers": sessions.aggregate(m=Max("peak_viewers"))["m"] or 0,
        "follower_count": Follow.objects.filter(followee=user).count(),
    }
