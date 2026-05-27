"""Services notifications (création synchrone, pas de dépendance worker)."""

from __future__ import annotations

from django.utils import timezone

from .models import Notification


def create_notification(recipient, type, actor=None, payload=None) -> Notification:
    return Notification.objects.create(
        recipient=recipient,
        type=type,
        actor=actor,
        payload=payload or {},
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
