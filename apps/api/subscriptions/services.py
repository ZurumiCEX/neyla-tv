"""Services abonnements : config du palier, souscription (Aura), annulation."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from channels_app.models import Channel

from .models import Subscription, SubTier

PERIOD_DAYS = 30


class SubscriptionError(Exception):
    """Erreur métier abonnement."""


def set_tier(
    channel: Channel,
    price_aura: int,
    perks: list,
    is_active: bool = True,
    badge_url: str = "",
    stickers_urls: list | None = None,
) -> SubTier:
    """Crée/maj le palier. Le nouveau prix ne s'applique qu'aux NOUVEAUX abonnés
    (les abonnés existants gardent `Subscription.price_paid`)."""
    from django.conf import settings

    max_price = int(getattr(settings, "SUB_TIER_MAX_AURA", 50_000))
    if int(price_aura) > max_price:
        raise SubscriptionError(f"Le prix d'un abonnement est plafonné à {max_price} Aura.")
    tier, _ = SubTier.objects.update_or_create(
        channel=channel,
        defaults={
            "price_aura": int(price_aura),
            "perks": perks or [],
            "badge_url": (badge_url or "").strip(),
            "stickers_urls": [s for s in (stickers_urls or []) if s],
            "is_active": is_active,
        },
    )
    return tier


def active_tier(channel: Channel) -> SubTier | None:
    return SubTier.objects.filter(channel=channel, is_active=True).order_by("id").first()


def _channel(slug: str) -> Channel:
    channel = Channel.objects.select_related("user").filter(slug=slug.lower()).first()
    if channel is None:
        raise SubscriptionError("Chaîne introuvable.")
    if not channel.is_provisioned:
        raise SubscriptionError("Cette chaîne ne propose pas encore d'abonnement.")
    return channel


def _next_period_end(existing: Subscription | None):
    """Prolonge depuis la fin de période en cours (aucun jour payé n'est perdu)."""
    now = timezone.now()
    base = existing.current_period_end if existing and existing.is_active else now
    return max(base, now) + timezone.timedelta(days=PERIOD_DAYS)


@transaction.atomic
def subscribe(user, channel_slug: str, idempotency_key: str | None = None) -> Subscription:
    """S'abonner (ou prolonger d'un mois) au prix actuel du palier.

    Un abonné déjà actif qui se réabonne PROLONGE sa période depuis sa date de
    fin (plus de remise à zéro) ; le renouvellement automatique est réactivé.
    """
    from payments.services import charge_subscription, recall, remember

    previous = recall(user, "subscribe", idempotency_key)
    if previous:
        found = Subscription.objects.filter(pk=previous, subscriber=user).first()
        if found is not None:
            return found
    channel = _channel(channel_slug)
    if channel.user_id == user.id:
        raise SubscriptionError("Tu ne peux pas t'abonner à toi-même.")
    tier = active_tier(channel)
    if tier is None:
        raise SubscriptionError("Aucun abonnement disponible sur cette chaîne.")

    existing = (
        Subscription.objects.select_for_update().filter(subscriber=user, channel=channel).first()
    )
    period_end = _next_period_end(existing)
    sub, _ = Subscription.objects.update_or_create(
        subscriber=user,
        channel=channel,
        defaults={
            "tier": tier,
            "status": Subscription.Status.ACTIVE,
            "started_at": (
                existing.started_at if existing and existing.is_active else timezone.now()
            ),
            "current_period_end": period_end,
            "price_paid": tier.price_aura,
            "cancel_at_period_end": False,
            "auto_renew": True,
            "gifted_by": None,
        },
    )
    charge_subscription(user, channel.user, tier.price_aura, related=sub)
    remember(user, "subscribe", idempotency_key, sub)
    transaction.on_commit(lambda: _after_subscribe(channel, user))
    return sub


def _after_subscribe(channel: Channel, user) -> None:
    import contextlib

    with contextlib.suppress(Exception):
        _notify(channel.user, user)
        from gamification.services import check_and_award

        check_and_award(user, "subscription")
    with contextlib.suppress(Exception):
        from safety.anticheat import evaluate_self_deal, evaluate_subscription

        evaluate_subscription(user, channel)
        evaluate_self_deal(user, channel)


@transaction.atomic
def gift_subscription(gifter, channel_slug: str, recipient_username: str) -> Subscription:
    """Offre un mois d'abonnement : débite l'offreur, abonne le destinataire.

    Un abonnement offert ne se renouvelle PAS automatiquement (le destinataire
    n'a rien choisi, et l'offreur ne doit pas être débité indéfiniment).
    Si le destinataire est déjà abonné, sa période est prolongée d'un mois.
    """
    from accounts.models import User
    from payments.services import charge_subscription

    channel = _channel(channel_slug)
    if channel.user_id == gifter.id:
        raise SubscriptionError("Tu ne peux pas offrir un abonnement à ta propre chaîne.")
    recipient = User.objects.filter(username__iexact=(recipient_username or "").strip()).first()
    if recipient is None:
        raise SubscriptionError("Destinataire introuvable.")
    if recipient.id == gifter.id:
        raise SubscriptionError("Tu ne peux pas t'offrir un abonnement à toi-même.")
    if recipient.id == channel.user_id:
        raise SubscriptionError("Le créateur ne peut pas recevoir un abonnement à sa chaîne.")
    tier = active_tier(channel)
    if tier is None:
        raise SubscriptionError("Aucun abonnement disponible sur cette chaîne.")

    existing = (
        Subscription.objects.select_for_update()
        .filter(subscriber=recipient, channel=channel)
        .first()
    )
    keeps_own_renewal = bool(existing and existing.is_active and existing.auto_renew)
    sub, _ = Subscription.objects.update_or_create(
        subscriber=recipient,
        channel=channel,
        defaults={
            "tier": tier,
            "gifted_by": gifter,
            "status": Subscription.Status.ACTIVE,
            "current_period_end": _next_period_end(existing),
            "price_paid": existing.price_paid if keeps_own_renewal else tier.price_aura,
            "auto_renew": keeps_own_renewal,
        },
    )
    charge_subscription(gifter, channel.user, tier.price_aura, related=sub)
    transaction.on_commit(
        lambda: (_notify(channel.user, recipient), _notify_gift(recipient, gifter, channel))
    )
    return sub


def _notify_gift(recipient, gifter, channel) -> None:
    from notifications.models import Notification
    from notifications.services import create_notification

    create_notification(
        recipient=recipient,
        type=Notification.Type.SUBSCRIPTION,
        actor=gifter,
        payload={
            "gifted": True,
            "gifter": gifter.username,
            "channel": channel.slug,
        },
    )


def cancel(user, channel_slug: str) -> int:
    """Annule le renouvellement : l'accès reste ouvert jusqu'à la fin de la période."""
    channel = Channel.objects.filter(slug=(channel_slug or "").lower()).first()
    if channel is None:
        return 0
    return Subscription.objects.filter(
        subscriber=user, channel=channel, status=Subscription.Status.ACTIVE
    ).update(cancel_at_period_end=True)


def resume(user, channel_slug: str) -> int:
    """Réactive le renouvellement d'un abonnement annulé mais encore actif."""
    channel = Channel.objects.filter(slug=(channel_slug or "").lower()).first()
    if channel is None:
        return 0
    return Subscription.objects.filter(
        subscriber=user,
        channel=channel,
        status=Subscription.Status.ACTIVE,
        current_period_end__gt=timezone.now(),
    ).update(cancel_at_period_end=False, auto_renew=True)


def is_subscribed(user, channel: Channel) -> bool:
    sub = Subscription.objects.filter(subscriber=user, channel=channel).first()
    return bool(sub and sub.is_active)


def subscriber_user_ids(channel: Channel) -> set[int]:
    """IDs des abonnés actifs (pour le badge chat)."""
    now = timezone.now()
    return set(
        Subscription.objects.filter(
            channel=channel,
            status=Subscription.Status.ACTIVE,
            current_period_end__gt=now,
        ).values_list("subscriber_id", flat=True)
    )


def _renew_one(sub_id: int, now) -> str:
    """Renouvelle/expire UN abonnement dans sa propre transaction (ligne verrouillée).

    `skip_locked` : deux exécutions concurrentes du batch ne traitent jamais la
    même ligne → pas de double débit. Retourne "renewed" | "expired" | "skipped".
    """
    from payments.services import InsufficientBalanceError, PaymentError, charge_subscription

    with transaction.atomic():
        sub = (
            Subscription.objects.select_for_update(skip_locked=True, of=("self",))
            .select_related("channel__user", "tier", "subscriber")
            .filter(pk=sub_id, status=Subscription.Status.ACTIVE, current_period_end__lte=now)
            .first()
        )
        if sub is None:
            return "skipped"
        tier_alive = bool(sub.tier and sub.tier.is_active)
        if sub.cancel_at_period_end or not sub.auto_renew or not tier_alive:
            sub.status = Subscription.Status.EXPIRED
            sub.save(update_fields=["status"])
            return "expired"
        price = sub.price_paid or sub.tier.price_aura
        try:
            with transaction.atomic():
                charge_subscription(sub.subscriber, sub.channel.user, price, related=sub)
        except (InsufficientBalanceError, PaymentError):
            sub.status = Subscription.Status.EXPIRED
            sub.save(update_fields=["status"])
            return "expired"
        sub.price_paid = price
        sub.current_period_end = now + timezone.timedelta(days=PERIOD_DAYS)
        sub.save(update_fields=["price_paid", "current_period_end"])
        return "renewed"


def process_due_subscriptions(now=None) -> dict:
    """Renouvelle (au prix verrouillé) ou expire les abonnements arrivés à échéance.

    Conçu pour le beat quotidien ou un cron ; sûr en exécutions concurrentes.
    """
    now = now or timezone.now()
    counts = {"renewed": 0, "expired": 0}
    due_ids = list(
        Subscription.objects.filter(
            status=Subscription.Status.ACTIVE, current_period_end__lte=now
        ).values_list("id", flat=True)
    )
    for sub_id in due_ids:
        result = _renew_one(sub_id, now)
        if result in counts:
            counts[result] += 1
    return counts


def _notify(creator, subscriber) -> None:
    from notifications.models import Notification
    from notifications.services import create_notification

    create_notification(
        recipient=creator,
        type=Notification.Type.SUBSCRIPTION,
        actor=subscriber,
        payload={"username": subscriber.username},
    )
