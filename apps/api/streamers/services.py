"""Logique métier des candidatures streamer (sans import DRF).

- submit_application : (re)dépose une candidature (réessai possible après rejet).
- approve_application : respecte le quota quotidien, puis déclenche le
  provisioning Cloudflare de la chaîne (réutilise channels_app).
- reject_application : refuse avec motif.
"""

from __future__ import annotations

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import StreamerApplication


class StreamerError(Exception):
    """Erreur métier côté candidatures streamer."""


class QuotaExceededError(StreamerError):
    """Quota quotidien d'approbations atteint."""


class AlreadyStreamerError(StreamerError):
    """L'utilisateur est déjà streamer approuvé."""


def submit_application(user, motivation: str = "") -> StreamerApplication:
    application, created = StreamerApplication.objects.get_or_create(
        user=user,
        defaults={"motivation": motivation},
    )
    if created:
        return application
    if application.status == StreamerApplication.Status.APPROVED:
        raise AlreadyStreamerError("Tu es déjà streamer.")
    # pending ou rejected → (re)met en attente avec la nouvelle motivation.
    application.status = StreamerApplication.Status.PENDING
    application.motivation = motivation or application.motivation
    application.decided_at = None
    application.decided_by = None
    application.rejection_reason = ""
    application.save()
    return application


def daily_quota_remaining() -> int:
    quota = getattr(settings, "STREAMER_DAILY_APPROVAL_QUOTA", 100)
    used = StreamerApplication.objects.filter(
        status=StreamerApplication.Status.APPROVED,
        decided_at__date=timezone.localdate(),
    ).count()
    return max(quota - used, 0)


def approve_application(application: StreamerApplication, admin) -> StreamerApplication:
    if application.status == StreamerApplication.Status.APPROVED:
        return application  # idempotent : ne reconsomme pas le quota
    with transaction.atomic():
        if daily_quota_remaining() <= 0:
            raise QuotaExceededError("Quota quotidien d'approbations atteint.")
        application.status = StreamerApplication.Status.APPROVED
        application.decided_at = timezone.now()
        application.decided_by = admin
        application.rejection_reason = ""
        application.save()
    _enqueue_provisioning(application.user_id)
    return application


def reject_application(
    application: StreamerApplication, admin, reason: str = ""
) -> StreamerApplication:
    application.status = StreamerApplication.Status.REJECTED
    application.decided_at = timezone.now()
    application.decided_by = admin
    application.rejection_reason = reason
    application.save()
    return application


def _enqueue_provisioning(user_id: int) -> None:
    """Provisionne la chaîne de l'utilisateur (réutilise la task channels_app)."""
    from channels_app.models import Channel
    from channels_app.tasks import provision_live_input_task

    channel = Channel.objects.filter(user_id=user_id).first()
    if channel is not None and not channel.is_provisioned:
        provision_live_input_task.delay(channel.id)
