"""Suivi des dons par chaîne (badges) et des dépenses à vie (niveaux)."""

from __future__ import annotations

from django.db.models import F
from django.utils import timezone

from .levels import GIFT_TIERS, LEVELS, gift_tier, level_for
from .models import ChannelSupport

# Écritures du grand livre qui comptent comme Aura « dépensée ».
SPEND_KINDS = {"tip_sent", "sub_paid", "charity_donation"}


def record_spend(user_id: int, amount: int) -> None:
    """Ajoute une dépense au total à vie (atomique, dans la transaction appelante)."""
    from accounts.models import User

    if amount > 0:
        User.objects.filter(pk=user_id).update(
            lifetime_aura_spent=F("lifetime_aura_spent") + int(amount)
        )


def record_support(user, channel, amount: int) -> ChannelSupport:
    """Ajoute un don (tip, abonnement offert) au total offert à cette chaîne."""
    support, _ = ChannelSupport.objects.get_or_create(user=user, channel=channel)
    ChannelSupport.objects.filter(pk=support.pk).update(
        total_aura=F("total_aura") + int(amount), last_gift_at=timezone.now()
    )
    support.refresh_from_db(fields=["total_aura", "last_gift_at"])
    return support


def support_total(user_id: int, channel_id: int) -> int:
    return (
        ChannelSupport.objects.filter(user_id=user_id, channel_id=channel_id)
        .values_list("total_aura", flat=True)
        .first()
        or 0
    )


def chat_badges(user_id: int, channel_id: int, lifetime_spent: int) -> dict:
    """Badges affichés dans le chat : niveau (global) + badge de don (cette chaîne)."""
    return {
        "level": level_for(lifetime_spent),
        "gift_tier": gift_tier(support_total(user_id, channel_id)),
    }


__all__ = [
    "GIFT_TIERS",
    "LEVELS",
    "SPEND_KINDS",
    "chat_badges",
    "record_spend",
    "record_support",
    "support_total",
]
