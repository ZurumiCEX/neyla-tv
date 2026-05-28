"""Tâches Celery notifications : emails best-effort (live d'une chaîne suivie)."""

from __future__ import annotations

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from social.models import Follow

from .models import Notification, NotificationPreference, PushSubscription


@shared_task
def email_live_followers(channel_id: int) -> int:
    """Email opt-in aux followers quand une chaîne suivie passe en direct.

    Opt-in = email vérifié + préférence LIVE_STARTED non désactivée.
    Best-effort : les échecs d'envoi n'interrompent pas le lot.
    """
    from channels_app.models import Channel

    channel = Channel.objects.filter(id=channel_id).select_related("user").first()
    if channel is None:
        return 0

    disabled_ids = set(
        NotificationPreference.objects.filter(
            type=Notification.Type.LIVE_STARTED, enabled=False
        ).values_list("user_id", flat=True)
    )
    recipients = (
        Follow.objects.filter(followee=channel.user, follower__email_verified_at__isnull=False)
        .exclude(follower_id__in=disabled_ids)
        .select_related("follower")
        .values_list("follower__email", flat=True)
    )

    name = channel.user.display_name or channel.user.username
    url = f"{settings.FRONTEND_URL}/c/{channel.slug}"
    sent = 0
    for email in recipients:
        if not email:
            continue
        send_mail(
            subject=f"{name} est en direct sur Neyla TV",
            message=f"{name} vient de lancer un live.\n\nRegarde maintenant : {url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
        sent += 1
    return sent


@shared_task
def push_live_followers(channel_id: int) -> int:
    """Web Push aux followers (préférence LIVE_STARTED active) quand la chaîne passe live."""
    from . import push

    if not push.is_configured():
        return 0

    from channels_app.models import Channel

    channel = Channel.objects.filter(id=channel_id).select_related("user").first()
    if channel is None:
        return 0

    disabled_ids = set(
        NotificationPreference.objects.filter(
            type=Notification.Type.LIVE_STARTED, enabled=False
        ).values_list("user_id", flat=True)
    )
    follower_ids = (
        Follow.objects.filter(followee=channel.user)
        .exclude(follower_id__in=disabled_ids)
        .values_list("follower_id", flat=True)
    )
    name = channel.user.display_name or channel.user.username
    payload = {
        "title": f"{name} est en direct",
        "body": channel.title or "Un live vient de commencer.",
        "url": f"/c/{channel.slug}",
    }
    sent = 0
    for sub in PushSubscription.objects.filter(user_id__in=list(follower_ids)):
        if push.send_to_subscription(sub, payload):
            sent += 1
    return sent
