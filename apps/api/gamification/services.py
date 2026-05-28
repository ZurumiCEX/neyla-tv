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
}


def sync_catalog() -> None:
    """Garantit l'existence des succès du catalogue (idempotent)."""
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
    }
    if event in simple:
        _award(user, simple[event])
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
