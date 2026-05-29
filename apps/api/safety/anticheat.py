"""Anti-triche / anti-fraude : détection des comportements qui faussent l'économie
ou les métriques (tips en rafale, follows en rafale, multi-comptes, gonflage).

Tous les détecteurs sont best-effort et ne lèvent jamais d'exception vers
l'appelant : une erreur de détection ne doit pas casser l'action légitime.
"""

from __future__ import annotations

import contextlib
import logging

from django.utils import timezone

from .models import RiskEvent

logger = logging.getLogger(__name__)

# Seuils (fenêtre glissante courte → rafale suspecte).
TIP_WINDOW_SECONDS = 60
TIP_MAX_PER_WINDOW = 8
FOLLOW_WINDOW_SECONDS = 60
FOLLOW_MAX_PER_WINDOW = 20

# Gonflage de vues : viewers anormalement élevés vs. base réelle (followers/IP).
VIEW_MIN_SUSPICIOUS = 50
VIEW_INFLATION_FACTOR = 5

# Abonnements : churn (ré-abonnements répétés) et rafale de subs côté créateur.
SUB_CHURN_WINDOW_SECONDS = 3600
SUB_CHURN_MAX = 5
SUB_CREATOR_WINDOW_SECONDS = 600
SUB_CREATOR_MAX = 15


def flag(user, kind: str, severity: int = RiskEvent.Severity.LOW, detail=None) -> RiskEvent | None:
    """Enregistre un signal de risque (idempotence souple par déduplication courte)."""
    try:
        return RiskEvent.objects.create(
            user=user, kind=kind, severity=severity, detail=detail or {}
        )
    except Exception:  # noqa: BLE001
        logger.debug("risk flag failed", exc_info=True)
        return None


def evaluate_tip(from_user, channel) -> None:
    """Tips en rafale depuis un même compte → signal de vélocité."""
    with contextlib.suppress(Exception):
        from payments.models import Tip

        since = timezone.now() - timezone.timedelta(seconds=TIP_WINDOW_SECONDS)
        count = Tip.objects.filter(from_user=from_user, created_at__gte=since).count()
        if count >= TIP_MAX_PER_WINDOW:
            sev = (
                RiskEvent.Severity.HIGH
                if count >= TIP_MAX_PER_WINDOW * 2
                else (RiskEvent.Severity.MEDIUM)
            )
            flag(
                from_user,
                RiskEvent.Kind.TIP_VELOCITY,
                sev,
                {"count": count, "window_s": TIP_WINDOW_SECONDS, "channel": channel.slug},
            )


def evaluate_follow(follower, target) -> None:
    """Follows en rafale → bot/ferme de comptes."""
    with contextlib.suppress(Exception):
        from social.models import Follow

        since = timezone.now() - timezone.timedelta(seconds=FOLLOW_WINDOW_SECONDS)
        count = Follow.objects.filter(follower=follower, created_at__gte=since).count()
        if count >= FOLLOW_MAX_PER_WINDOW:
            flag(
                follower,
                RiskEvent.Kind.FOLLOW_VELOCITY,
                RiskEvent.Severity.MEDIUM,
                {"count": count, "window_s": FOLLOW_WINDOW_SECONDS, "target": target.username},
            )


def evaluate_multi_account(channel, user, ip: str | None) -> None:
    """Plusieurs comptes distincts depuis une même IP sur une chaîne → suspicion."""
    if not ip:
        return
    with contextlib.suppress(Exception):
        from chat.models import ChatUserIp

        distinct_users = (
            ChatUserIp.objects.filter(channel=channel, ip=ip)
            .values_list("user_id", flat=True)
            .distinct()
        )
        users = set(distinct_users) | {user.id}
        if len(users) >= 4:
            flag(
                user,
                RiskEvent.Kind.MULTI_ACCOUNT,
                RiskEvent.Severity.MEDIUM,
                {"ip": ip, "accounts": len(users), "channel": channel.slug},
            )


def evaluate_view_inflation(channel, viewers: int) -> None:
    """Viewers concurrents très supérieurs à la base réelle (followers / IP distinctes)."""
    if viewers < VIEW_MIN_SUSPICIOUS:
        return
    with contextlib.suppress(Exception):
        from chat.models import ChatUserIp
        from social.models import Follow

        followers = Follow.objects.filter(followee=channel.user).count()
        distinct_ips = ChatUserIp.objects.filter(channel=channel).values("ip").distinct().count()
        baseline = max(followers, distinct_ips, 1)
        if viewers > baseline * VIEW_INFLATION_FACTOR:
            sev = (
                RiskEvent.Severity.HIGH
                if viewers > baseline * VIEW_INFLATION_FACTOR * 2
                else RiskEvent.Severity.MEDIUM
            )
            flag(
                channel.user,
                RiskEvent.Kind.VIEW_INFLATION,
                sev,
                {
                    "viewers": viewers,
                    "followers": followers,
                    "distinct_ips": distinct_ips,
                    "channel": channel.slug,
                },
            )


def evaluate_subscription(subscriber, channel) -> None:
    """Churn d'abonnement (ré-abonnements répétés) + rafale de subs côté créateur."""
    with contextlib.suppress(Exception):
        from payments.models import LedgerEntry

        # Churn côté abonné : nombre de paiements d'abonnement sur une fenêtre.
        since = timezone.now() - timezone.timedelta(seconds=SUB_CHURN_WINDOW_SECONDS)
        paid = LedgerEntry.objects.filter(
            wallet__user=subscriber,
            kind=LedgerEntry.Kind.SUB_PAID,
            created_at__gte=since,
        ).count()
        if paid >= SUB_CHURN_MAX:
            flag(
                subscriber,
                RiskEvent.Kind.SUB_ABUSE,
                RiskEvent.Severity.MEDIUM,
                {"sub_payments": paid, "window_s": SUB_CHURN_WINDOW_SECONDS},
            )

    with contextlib.suppress(Exception):
        from subscriptions.models import Subscription

        # Rafale côté créateur : nouveaux abonnements gagnés sur une courte fenêtre.
        since = timezone.now() - timezone.timedelta(seconds=SUB_CREATOR_WINDOW_SECONDS)
        gained = Subscription.objects.filter(channel=channel, started_at__gte=since).count()
        if gained >= SUB_CREATOR_MAX:
            flag(
                channel.user,
                RiskEvent.Kind.SUB_ABUSE,
                RiskEvent.Severity.HIGH,
                {
                    "new_subs": gained,
                    "window_s": SUB_CREATOR_WINDOW_SECONDS,
                    "channel": channel.slug,
                },
            )
