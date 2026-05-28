"""Services abonnements : config du palier, souscription (Aura), annulation."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from channels_app.models import Channel

from .models import Subscription, SubTier

PERIOD_DAYS = 30


class SubscriptionError(Exception):
    """Erreur métier abonnement."""


def set_tier(channel: Channel, price_aura: int, perks: list, is_active: bool = True) -> SubTier:
    tier, _ = SubTier.objects.update_or_create(
        channel=channel,
        defaults={
            "price_aura": int(price_aura),
            "perks": perks or [],
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
    return sub


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


def _notify(creator, subscriber) -> None:
    from notifications.models import Notification
    from notifications.services import create_notification

    create_notification(
        recipient=creator,
        type=Notification.Type.SUBSCRIPTION,
        actor=subscriber,
        payload={"username": subscriber.username},
    )
