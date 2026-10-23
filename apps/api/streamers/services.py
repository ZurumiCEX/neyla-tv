"""Logique métier des candidatures streamer (sans import DRF).

- submit_application : (re)dépose une candidature (réessai possible après rejet).
- approve_application : respecte le quota quotidien, puis déclenche le
  provisioning Bunny Stream de la chaîne (réutilise channels_app).
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


# Champs de candidature acceptés depuis l'API (le reste est ignoré).
_APPLICATION_FIELDS = frozenset(
    {
        "full_name",
        "country",
        "primary_language",
        "main_games",
        "content_categories",
        "goals",
        "community_type",
        "has_streamed",
        "platforms",
        "community_size",
        "frequency",
        "avg_duration",
        "setup",
        "connection_quality",
        "why_select",
        "what_bring",
        "intro_video_url",
        "setup_screenshot_url",
        "rules_accepted",
    }
)


def submit_application(
    user, motivation: str = "", fields: dict | None = None
) -> StreamerApplication:
    """(Re)dépose une candidature détaillée et calcule son score automatique."""
    from .scoring import compute_score

    fields = fields or {}
    application, created = StreamerApplication.objects.get_or_create(
        user=user,
        defaults={"motivation": motivation},
    )
    if not created and application.status == StreamerApplication.Status.APPROVED:
        raise AlreadyStreamerError("Tu es déjà streamer.")

    if motivation:
        application.motivation = motivation
    for key, value in fields.items():
        if key in _APPLICATION_FIELDS:
            setattr(application, key, value)

    # (re)met en attente : pending au 1er dépôt comme après un rejet.
    application.status = StreamerApplication.Status.PENDING
    application.decided_at = None
    application.decided_by = None
    application.rejection_reason = ""
    application.score = compute_score(application)
    application.save()

    if created:
        from gamification.services import check_and_award

        check_and_award(user, "first_application")
    return application


def set_under_review(application: StreamerApplication, admin) -> StreamerApplication:
    application.status = StreamerApplication.Status.UNDER_REVIEW
    application.save(update_fields=["status", "updated_at"])
    _audit(admin, "streamer.under_review", application)
    return application


def request_interview(application: StreamerApplication, admin) -> StreamerApplication:
    application.status = StreamerApplication.Status.INTERVIEW
    application.save(update_fields=["status", "updated_at"])
    _notify_decision(application, "interview")
    _audit(admin, "streamer.interview", application)
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
    provisioned = _provision_channel_now(application.user_id)
    _notify_decision(application, "approved")
    _audit(admin, "streamer.approve", application)
    if not provisioned:
        # Le flux sera recréé à la prochaine ouverture du dashboard (réconciliation).
        _audit(admin, "streamer.provision_failed", application)
    return application


def reject_application(
    application: StreamerApplication, admin, reason: str = ""
) -> StreamerApplication:
    application.status = StreamerApplication.Status.REJECTED
    application.decided_at = timezone.now()
    application.decided_by = admin
    application.rejection_reason = reason
    application.save()
    _notify_decision(application, "rejected")
    _audit(admin, "streamer.reject", application)
    return application


def _audit(admin, action: str, application: StreamerApplication) -> None:
    from audit.services import record

    record(admin, action, target=application.user, meta={"application": application.id})


def _notify_decision(application: StreamerApplication, status: str) -> None:
    from notifications.models import Notification
    from notifications.services import create_notification

    create_notification(
        recipient=application.user,
        type=Notification.Type.APPLICATION_DECIDED,
        payload={"status": status, "reason": application.rejection_reason},
    )


def _provision_channel_now(user_id: int) -> bool:
    """Provisionne la chaîne de façon SYNCHRONE (aucune dépendance au worker Celery).

    L'approbation reste fonctionnelle même si le worker est indisponible ou si
    Bunny échoue : l'échec est journalisé, la notification part quand même et la
    réconciliation du dashboard réessaiera. provision_channel est idempotent.
    Retourne True si la chaîne est provisionnée à l'issue de l'appel.
    """
    import logging

    from channels_app.bunny import BunnyStreamError
    from channels_app.models import Channel
    from channels_app.services import provision_channel

    channel = Channel.objects.filter(user_id=user_id).first()
    if channel is None:
        return False
    if channel.is_provisioned:
        return True
    try:
        provision_channel(channel)
    except BunnyStreamError:
        logging.getLogger(__name__).exception("provisioning Bunny échoué (user %s)", user_id)
        return False
    return True
