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
    return channel


@transaction.atomic
def subscribe(user, channel_slug: str) -> Subscription:
    channel = _channel(channel_slug)
    if channel.user_id == user.id:
        raise SubscriptionError("Tu ne peux pas t'abonner à toi-même.")
    tier = active_tier(channel)
    if tier is None:
        raise SubscriptionError("Aucun abonnement disponible sur cette chaîne.")

    from payments.services import charge_subscription

    charge_subscription(user, channel.user, tier.price_aura)

    now = timezone.now()
    sub, _ = Subscription.objects.update_or_create(
        subscriber=user,
        channel=channel,
        defaults={
            "tier": tier,
            "status": Subscription.Status.ACTIVE,
            "started_at": now,
            "current_period_end": now + timezone.timedelta(days=PERIOD_DAYS),
        },
    )
    _notify(channel.user, user)
    from gamification.services import check_and_award

    check_and_award(user, "subscription")

    import contextlib

    with contextlib.suppress(Exception):
        from safety.anticheat import evaluate_self_deal, evaluate_subscription

        evaluate_subscription(user, channel)
        evaluate_self_deal(user, channel)
    return sub


@transaction.atomic
def gift_subscription(gifter, channel_slug: str, recipient_username: str) -> Subscription:
    """Offre un abonnement : débite l'offreur en Aura, abonne le destinataire.

    Refuse : s'offrir à soi, offreur == créateur, destinataire = créateur,
    destinataire introuvable, solde insuffisant (remonte ``PaymentError``).
    """
    from accounts.models import User

    channel = _channel(channel_slug)
    if channel.user_id == gifter.id:
        raise SubscriptionError("Tu ne peux pas offrir un abonnement à ta propre chaîne.")
    recipient = User.objects.filter(username=(recipient_username or "").strip().lower()).first()
    if recipient is None:
        raise SubscriptionError("Destinataire introuvable.")
    if recipient.id == gifter.id:
        raise SubscriptionError("Tu ne peux pas t'offrir un abonnement à toi-même.")
    if recipient.id == channel.user_id:
        raise SubscriptionError("Le créateur ne peut pas recevoir un abonnement à sa chaîne.")
    tier = active_tier(channel)
    if tier is None:
        raise SubscriptionError("Aucun abonnement disponible sur cette chaîne.")

    from payments.services import charge_subscription

    charge_subscription(gifter, channel.user, tier.price_aura)

    now = timezone.now()
    sub, _ = Subscription.objects.update_or_create(
        subscriber=recipient,
        channel=channel,
        defaults={
            "tier": tier,
            "gifted_by": gifter,
            "status": Subscription.Status.ACTIVE,
            "started_at": now,
            "current_period_end": now + timezone.timedelta(days=PERIOD_DAYS),
        },
    )
    _notify(channel.user, recipient)
    _notify_gift(recipient, gifter, channel)
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
    channel = _channel(channel_slug)
    return Subscription.objects.filter(subscriber=user, channel=channel).update(
        status=Subscription.Status.CANCELED
    )


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


def process_due_subscriptions(now=None) -> dict:
    """Renouvelle ou expire les abonnements actifs arrivés à échéance.

    Renouvelle en débitant le wallet (palier toujours actif + solde suffisant),
    sinon passe l'abonnement en EXPIRED. Conçu pour un beat task ou un cron ;
    fonctionne aussi en exécution manuelle (repli sans worker).
    """
    from payments.services import InsufficientBalanceError, PaymentError, charge_subscription

    now = now or timezone.now()
    renewed = 0
    expired = 0
    due = Subscription.objects.select_related("channel__user", "tier", "subscriber").filter(
        status=Subscription.Status.ACTIVE, current_period_end__lte=now
    )
    for sub in due:
        tier = sub.tier if (sub.tier and sub.tier.is_active) else active_tier(sub.channel)
        if tier is None:
            sub.status = Subscription.Status.EXPIRED
            sub.save(update_fields=["status"])
            expired += 1
            continue
        try:
            charge_subscription(sub.subscriber, sub.channel.user, tier.price_aura)
        except (InsufficientBalanceError, PaymentError):
            sub.status = Subscription.Status.EXPIRED
            sub.save(update_fields=["status"])
            expired += 1
            continue
        sub.tier = tier
        sub.current_period_end = now + timezone.timedelta(days=PERIOD_DAYS)
        sub.save(update_fields=["tier", "current_period_end"])
        renewed += 1
    return {"renewed": renewed, "expired": expired}


def _notify(creator, subscriber) -> None:
    from notifications.models import Notification
    from notifications.services import create_notification

    create_notification(
        recipient=creator,
        type=Notification.Type.SUBSCRIPTION,
        actor=subscriber,
        payload={"username": subscriber.username},
    )
