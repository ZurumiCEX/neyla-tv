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


_PERIOD_DEFAULTS = {"day": 30, "week": 12, "month": 12}


def _bucket_key(dt, period: str) -> str:
    local = timezone.localtime(dt).date()
    if period == "day":
        return local.isoformat()
    if period == "week":
        monday = local - timedelta(days=local.weekday())
        return monday.isoformat()
    # month
    return local.strftime("%Y-%m")


def _period_starts(period: str, n: int) -> list[str]:
    """Liste des clés ordonnées des N dernières périodes (jour/semaine/mois)."""
    today = timezone.localtime(timezone.now()).date()
    keys: list[str] = []
    if period == "day":
        for i in range(n - 1, -1, -1):
            keys.append((today - timedelta(days=i)).isoformat())
    elif period == "week":
        monday = today - timedelta(days=today.weekday())
        for i in range(n - 1, -1, -1):
            keys.append((monday - timedelta(weeks=i)).isoformat())
    else:  # month
        year, month = today.year, today.month
        months: list[tuple[int, int]] = []
        for _ in range(n):
            months.append((year, month))
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        for y, m in reversed(months):
            keys.append(f"{y:04d}-{m:02d}")
    return keys


def creator_revenue(user, period: str = "day", n: int | None = None) -> dict:
    """Revenus consolidés du créateur (tips + abonnements + parrainage) par période.

    Buckets Python (agnostique SGBD), même approche que ``_revenue_series``.
    Inclut aussi des totaux jour/semaine/mois et le solde retirable courant.
    """
    from payments.models import LedgerEntry
    from payments.services import withdrawable_balance

    period = period if period in _PERIOD_DEFAULTS else "day"
    n = n or _PERIOD_DEFAULTS[period]
    n = max(1, min(int(n), 90))

    keys = _period_starts(period, n)
    buckets: dict[str, dict] = {
        k: {"date": k, "tips": 0, "subs": 0, "referral": 0, "total": 0} for k in keys
    }
    valid_keys = set(buckets.keys())

    # Première période → début (utilisé pour limiter la requête).
    if period == "day":
        since = timezone.now() - timedelta(days=n - 1)
    elif period == "week":
        since = timezone.now() - timedelta(weeks=n - 1, days=timezone.localtime().weekday())
    else:
        since = timezone.now() - timedelta(days=31 * n)

    kinds = (
        LedgerEntry.Kind.TIP_RECEIVED,
        LedgerEntry.Kind.SUB_EARNED,
        LedgerEntry.Kind.REFERRAL,
    )
    entries = LedgerEntry.objects.filter(
        wallet__user=user, kind__in=kinds, created_at__gte=since
    ).only("kind", "amount", "created_at")

    for e in entries:
        key = _bucket_key(e.created_at, period)
        if key not in valid_keys:
            continue
        b = buckets[key]
        amt = int(e.amount)
        if e.kind == LedgerEntry.Kind.TIP_RECEIVED:
            b["tips"] += amt
        elif e.kind == LedgerEntry.Kind.SUB_EARNED:
            b["subs"] += amt
        elif e.kind == LedgerEntry.Kind.REFERRAL:
            b["referral"] += amt
        b["total"] += amt

    series = [buckets[k] for k in keys]
    totals = {
        "tips": sum(b["tips"] for b in series),
        "subs": sum(b["subs"] for b in series),
        "referral": sum(b["referral"] for b in series),
        "total": sum(b["total"] for b in series),
    }

    # Totaux 24h / 7j / 30j (toujours en jours) pour les cartes résumé.
    from django.db.models import Sum

    now = timezone.now()
    summary = {}
    for label, days in (("day", 1), ("week", 7), ("month", 30)):
        floor = now - timedelta(days=days)
        summary[label] = int(
            LedgerEntry.objects.filter(
                wallet__user=user, kind__in=kinds, created_at__gte=floor
            ).aggregate(s=Sum("amount"))["s"]
            or 0
        )

    return {
        "period": period,
        "series": series,
        "totals": totals,
        "summary": summary,
        "withdrawable": withdrawable_balance(user),
    }


def admin_dashboard_metrics(days: int = 30) -> dict:
    """Agrégat complet pour le tableau de bord du Django admin (KPIs + séries)."""
    from django.db.models import Q

    from catalog.models import Game
    from channels_app.models import Channel
    from gamification.models import UserAchievement
    from moderation.models import Report
    from payments.models import Payout, Purchase, Tip
    from safety.models import ContentFlag, RiskEvent
    from social.models import Follow
    from streamers.models import StreamerApplication
    from subscriptions.models import Subscription

    overview = platform_overview()
    growth = growth_metrics()
    window = max(1, min(days, 90))
    revenue = _revenue_series(window)
    since = timezone.now() - timedelta(days=window)
    paid = Purchase.objects.filter(status=Purchase.Status.PAID, created_at__gte=since)

    live = list(
        Channel.objects.filter(is_live=True)
        .select_related("user", "category")
        .annotate(followers=Count("user__followers", distinct=True))
        .order_by("-followers")[:8]
    )
    live_channels = [
        {
            "username": c.user.username,
            "followers": c.followers,
            "category": c.category.name if c.category_id else "—",
        }
        for c in live
    ]
    top_games = [
        {"name": g.name, "channels": g.n_channels, "live": g.n_live}
        for g in Game.objects.annotate(
            n_channels=Count("channels", distinct=True),
            n_live=Count("channels", filter=Q(channels__is_live=True), distinct=True),
        ).order_by("-n_channels")[:6]
    ]
    return {
        "overview": overview,
        "growth": growth,
        "revenue": revenue,
        "new_users_series": _daily_new_users(window),
        "commerce": {
            "paying_users": paid.values("user").distinct().count(),
            "purchases_count": paid.count(),
            "tips_count": Tip.objects.filter(created_at__gte=since).count(),
        },
        "content": {
            "follows_total": Follow.objects.count(),
            "subscriptions_active": Subscription.objects.filter(
                status=Subscription.Status.ACTIVE
            ).count(),
            "games_count": Game.objects.count(),
            "apps_pending": StreamerApplication.objects.filter(
                status=StreamerApplication.Status.PENDING
            ).count(),
            "achievements_unlocked": UserAchievement.objects.count(),
        },
        "live": {"channels": live_channels, "top_games": top_games},
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
