"""Services notifications (création synchrone, pas de dépendance worker)."""

from __future__ import annotations

from django.utils import timezone

from .models import Notification, NotificationPreference


def is_enabled(user, type) -> bool:
    """Une notification est activée sauf si une préférence explicite la désactive."""
    pref = NotificationPreference.objects.filter(user=user, type=type).first()
    return pref is None or pref.enabled


def create_notification(recipient, type, actor=None, payload=None) -> Notification | None:
    if not is_enabled(recipient, type):
        return None
    return Notification.objects.create(
        recipient=recipient,
        type=type,
        actor=actor,
        payload=payload or {},
    )


def get_preferences(user) -> dict:
    """État par type (activé par défaut), surchargé par les préférences stockées."""
    prefs = dict(NotificationPreference.objects.filter(user=user).values_list("type", "enabled"))
    return {t.value: prefs.get(t.value, True) for t in Notification.Type}


def set_preferences(user, mapping: dict) -> dict:
    valid = {t.value for t in Notification.Type}
    for type_key, enabled in mapping.items():
        if type_key in valid:
            NotificationPreference.objects.update_or_create(
                user=user, type=type_key, defaults={"enabled": bool(enabled)}
            )
    return get_preferences(user)


def send_support_message(recipient, title: str, body: str, sender=None) -> Notification | None:
    """Message support/système (équipe → utilisateur) sous forme de notification."""
    return create_notification(
        recipient=recipient,
        type=Notification.Type.SUPPORT_MESSAGE,
        actor=sender,
        payload={"title": title, "body": body},
    )


def notify_followers_live(channel) -> int:
    """Crée une notif "live démarré" pour chaque follower (bulk, synchrone)."""
    from social.models import Follow

    follower_ids = Follow.objects.filter(followee=channel.user).values_list(
        "follower_id", flat=True
    )
    payload = {
        "slug": channel.slug,
        "display_name": channel.user.display_name or channel.user.username,
    }
    notifications = [
        Notification(
            recipient_id=fid,
            type=Notification.Type.LIVE_STARTED,
            actor=channel.user,
            payload=payload,
        )
        for fid in follower_ids
    ]
    Notification.objects.bulk_create(notifications)
    return len(notifications)


def mark_read(user, ids=None) -> int:
    qs = Notification.objects.filter(recipient=user, read_at__isnull=True)
    if ids:
        qs = qs.filter(id__in=ids)
    return qs.update(read_at=timezone.now())
