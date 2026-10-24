"""Attribution des succès. `check_and_award` est sûr : il n'interrompt jamais l'appelant.

Les hooks sont synchrones (repli sans worker). Chaque succès « première fois » est
idempotent grâce à la contrainte d'unicité (user, achievement).
"""

from __future__ import annotations

import logging

from .models import Achievement, UserAchievement

logger = logging.getLogger(__name__)

# clé -> (nom, description, icône, ordre)
CATALOG: dict[str, tuple[str, str, str, int]] = {
    "first_login": ("Bienvenue", "Première connexion à Neyla TV", "👋", 1),
    "first_application": ("Candidat", "Première candidature streamer", "📝", 2),
    "first_stream": ("Premier live", "Tu as lancé ton premier direct", "🎬", 3),
    "followers_50": ("Étoile montante", "50 personnes te suivent", "⭐", 4),
    "followers_100": ("Star", "100 personnes te suivent", "🌟", 5),
    "first_tip_sent": ("Généreux", "Premier tip envoyé", "💸", 6),
    "first_tip_received": ("Soutenu", "Premier tip reçu", "💰", 7),
    "first_subscription": ("Membre", "Premier abonnement souscrit", "💜", 8),
    "first_gift_sub": ("Cadeau !", "Premier abonnement offert à un autre spectateur", "🎁", 9),
    "first_charity": ("Grand cœur", "Premier don au Charity Day", "💗", 10),
    "follows_10": ("Explorateur", "Tu suis 10 chaînes", "🧭", 11),
    # Badges de don : total offert à une même chaîne.
    "gift_spark": ("Premier soutien", "1 Aura offerte à une chaîne", "✨", 20),
    "gift_glow": ("Fan fidèle", "100 Aura offertes à une même chaîne", "💜", 21),
    "gift_radiant": ("Mécène", "1 000 Aura offertes à une même chaîne", "💎", 22),
    "gift_nova": ("Grand mécène", "5 000 Aura offertes à une même chaîne", "🌟", 23),
    "gift_supreme": ("Légende", "10 000 Aura offertes à une même chaîne", "🔥", 24),
    # Niveaux : Aura dépensée à vie.
    "level_beginner": ("Beginner", "10 000 Aura dépensées sur Neyla", "🎮", 30),
    "level_casual": ("Casual Gamer", "50 000 Aura dépensées sur Neyla", "🕹️", 31),
    "level_great": ("Great Gamer", "100 000 Aura dépensées sur Neyla", "🏅", 32),
    "level_lord": ("Lord Gamer", "200 000 Aura dépensées sur Neyla", "👑", 33),
    "level_mvp": ("MVP Gamer", "500 000 Aura dépensées sur Neyla", "🏆", 34),
    "level_goat": ("G.O.A.T", "1 000 000 Aura dépensées sur Neyla", "🐐", 35),
}


def sync_catalog() -> None:
    """Garantit l'existence des succès du catalogue (idempotent, 1 requête si complet)."""
    if Achievement.objects.filter(key__in=CATALOG.keys()).count() == len(CATALOG):
        return
    for key, (name, description, icon, order) in CATALOG.items():
        Achievement.objects.get_or_create(
            key=key,
            defaults={"name": name, "description": description, "icon": icon, "order": order},
        )


def _award(user, key: str) -> UserAchievement | None:
    meta = CATALOG.get(key)
    if meta is None:
        return None
    name, description, icon, order = meta
    achievement, _ = Achievement.objects.get_or_create(
        key=key,
        defaults={"name": name, "description": description, "icon": icon, "order": order},
    )
    obj, created = UserAchievement.objects.get_or_create(user=user, achievement=achievement)
    if created:
        _notify(user, achievement)
        return obj
    return None


def _notify(user, achievement: Achievement) -> None:
    from notifications.models import Notification
    from notifications.services import create_notification

    create_notification(
        recipient=user,
        type=Notification.Type.ACHIEVEMENT,
        payload={"key": achievement.key, "name": achievement.name, "icon": achievement.icon},
    )


def _dispatch(user, event: str, **ctx) -> None:
    simple = {
        "first_login": "first_login",
        "first_application": "first_application",
        "first_stream": "first_stream",
        "tip_sent": "first_tip_sent",
        "tip_received": "first_tip_received",
        "subscription": "first_subscription",
        "gift_sub": "first_gift_sub",
        "charity": "first_charity",
    }
    if event in simple:
        _award(user, simple[event])
        return
    if event == "support":
        from .levels import GIFT_TIERS
        from .support import support_total

        channel = ctx.get("channel")
        total = support_total(user.pk, channel.pk) if channel is not None else 0
        for threshold, key in GIFT_TIERS:
            if total >= threshold:
                _award(user, f"gift_{key}")
        return
    if event == "spend":
        from accounts.models import User

        from .levels import LEVELS

        spent = User.objects.filter(pk=user.pk).values_list("lifetime_aura_spent", flat=True)
        spent = spent.first() or 0
        for threshold, key in LEVELS:
            if spent >= threshold:
                _award(user, f"level_{key}")
        return
    if event == "follow_given":
        from social.models import Follow

        if Follow.objects.filter(follower=user).count() >= 10:
            _award(user, "follows_10")
        return
    if event == "follow_received":
        count = ctx.get("follower_count")
        if count is None:
            from social.models import Follow

            count = Follow.objects.filter(followee=user).count()
        if count >= 100:
            _award(user, "followers_100")
        if count >= 50:
            _award(user, "followers_50")


def check_and_award(user, event: str, **ctx) -> None:
    """Évalue un événement et attribue les succès. Ne lève jamais (best-effort)."""
    if user is None:
        return
    try:
        _dispatch(user, event, **ctx)
    except Exception:
        # Un succès ne doit jamais casser le flux métier appelant.
        logger.exception("gamification.check_and_award failed: event=%s", event)
