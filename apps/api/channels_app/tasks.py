"""Tâches Celery du domaine Channels."""

from __future__ import annotations

import logging

from celery import shared_task

from .models import Channel
from .services import provision_channel

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def provision_live_input_task(self, channel_id: int) -> None:  # noqa: ARG001
    channel = Channel.objects.filter(pk=channel_id).first()
    if channel is None:
        logger.warning("provision_live_input_task: channel %s introuvable", channel_id)
        return
    provision_channel(channel)


@shared_task
def notify_followers_live_started(channel_id: int) -> None:
    """Phase 5 : on logue les followers concernés. L'envoi réel (email/push web)
    est reporté à une phase ultérieure — cf. ADR 006."""
    from social.models import Follow

    channel = Channel.objects.select_related("user").filter(pk=channel_id).first()
    if channel is None:
        return
    follower_ids = list(
        Follow.objects.filter(followee=channel.user).values_list("follower_id", flat=True)
    )
    if not follower_ids:
        return
    logger.info(
        "notify_followers_live_started channel=%s streamer=%s followers=%s",
        channel_id,
        channel.user.username,
        len(follower_ids),
    )
