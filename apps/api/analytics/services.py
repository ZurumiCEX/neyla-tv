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


def _revenue_series(days: int) -> dict:
    """Séries quotidiennes de revenus (bucket Python, agnostique du SGBD)."""
    from payments.models import Payout, Purchase, Tip
    from subscriptions.models import Subscription

    now = timezone.now()
    since = now - timedelta(days=days - 1)
    start_day = timezone.localtime(since).date()
    buckets: dict = {
        (start_day + timedelta(days=i)).isoformat(): {
            "date": (start_day + timedelta(days=i)).isoformat(),
            "purchases_xof": 0,
            "tips_aura": 0,
            "subs_aura": 0,
            "platform_commission_aura": 0,
            "payouts_aura": 0,
        }
        for i in range(days)
    }

    def bucket(dt):
        return buckets.get(timezone.localtime(dt).date().isoformat())

    totals = {
        "purchases_xof": 0,
        "tips_aura": 0,
        "subs_aura": 0,
        "platform_commission_aura": 0,
        "payouts_aura": 0,
    }
    for p in Purchase.objects.filter(status=Purchase.Status.PAID, created_at__gte=since):
        b = bucket(p.created_at)
        if b:
            b["purchases_xof"] += int(p.fiat_amount)
        totals["purchases_xof"] += int(p.fiat_amount)
    for t in Tip.objects.filter(created_at__gte=since):
        b = bucket(t.created_at)
        if b:
            b["tips_aura"] += t.aura_amount
            b["platform_commission_aura"] += t.platform_fee
        totals["tips_aura"] += t.aura_amount
        totals["platform_commission_aura"] += t.platform_fee
    for s in Subscription.objects.select_related("tier").filter(created_at__gte=since):
        amount = s.tier.price_aura if s.tier else 0
        b = bucket(s.created_at)
        if b:
            b["subs_aura"] += amount
        totals["subs_aura"] += amount
    for po in Payout.objects.filter(created_at__gte=since):
        b = bucket(po.created_at)
        if b:
            b["payouts_aura"] += po.aura_amount
        totals["payouts_aura"] += po.aura_amount

    return {"series": list(buckets.values()), "totals": totals}


def growth_metrics() -> dict:
    """Croissance & rétention : nouveaux inscrits + utilisateurs récurrents."""
    now = timezone.now()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    active_7d = User.objects.filter(last_active_at__gte=week_ago)
    return {
        "new_users_7d": User.objects.filter(date_joined__gte=week_ago).count(),
        "new_users_30d": User.objects.filter(date_joined__gte=month_ago).count(),
        # Récurrents : actifs cette semaine et inscrits il y a plus d'une semaine.
        "returning_users_7d": active_7d.filter(date_joined__lt=week_ago).count(),
        "active_7d": active_7d.count(),
    }


def admin_dashboard(days: int = 14) -> dict:
    """Vue d'ensemble + activité + progression des revenus pour l'admin."""
    return {
        "overview": platform_overview(),
        "growth": growth_metrics(),
        "revenue": _revenue_series(max(1, min(days, 90))),
    }


def _redis_ok() -> bool:
    import redis
    from django.conf import settings

    try:
        client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        return bool(client.ping())
    except Exception:
        return False


def _db_ok() -> bool:
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception:
        return False


def monitoring() -> dict:
    """État temps réel de la plateforme (santé services + activité live)."""
    from payments.models import Payout
    from subscriptions.models import Subscription

    now = timezone.now()
    live_channels = (
        Channel.objects.select_related("user")
        .filter(is_live=True)
        .order_by("-last_live_started_at")[:20]
    )
    return {
        "checked_at": now.isoformat(),
        "online_users": User.objects.filter(last_active_at__gte=now - timedelta(minutes=5)).count(),
        "live_now": Channel.objects.filter(is_live=True).count(),
        "active_subscriptions": Subscription.objects.filter(
            status=Subscription.Status.ACTIVE
        ).count(),
        "pending_payouts": Payout.objects.filter(status=Payout.Status.REQUESTED).count(),
        "services": {
            "database": _db_ok(),
            "redis": _redis_ok(),
        },
        "live_channels": [
            {
                "slug": c.slug,
                "username": c.user.username,
                "started_at": c.last_live_started_at,
            }
            for c in live_channels
        ],
    }


def _daily_new_users(days: int) -> list[dict]:
    """Série quotidienne d'inscriptions (bucket Python, agnostique du SGBD)."""
    now = timezone.now()
    since = now - timedelta(days=days - 1)
    start_day = timezone.localtime(since).date()
    buckets = {(start_day + timedelta(days=i)).isoformat(): 0 for i in range(days)}
    for u in User.objects.filter(date_joined__gte=since).only("date_joined"):
        key = timezone.localtime(u.date_joined).date().isoformat()
        if key in buckets:
            buckets[key] += 1
    return [{"date": d, "count": c} for d, c in buckets.items()]


def admin_dashboard_metrics(days: int = 30) -> dict:
    """Agrégat complet pour le tableau de bord du Django admin (KPIs + séries)."""
    from moderation.models import Report
    from payments.models import Payout
    from safety.models import ContentFlag, RiskEvent

    overview = platform_overview()
    growth = growth_metrics()
    revenue = _revenue_series(max(1, min(days, 90)))
    return {
        "overview": overview,
        "growth": growth,
        "revenue": revenue,
        "new_users_series": _daily_new_users(max(1, min(days, 90))),
        "moderation": {
            "open_reports": Report.objects.filter(status=Report.Status.OPEN).count(),
            "pending_flags": ContentFlag.objects.filter(status=ContentFlag.Status.PENDING).count(),
            "auto_blocked": ContentFlag.objects.filter(
                status=ContentFlag.Status.AUTO_BLOCKED
            ).count(),
            "open_risk": RiskEvent.objects.filter(resolved=False).count(),
            "pending_payouts": Payout.objects.filter(status=Payout.Status.REQUESTED).count(),
        },
    }
