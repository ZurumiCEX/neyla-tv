"""Tâches Celery du domaine Channels."""

from __future__ import annotations

import logging

from celery import shared_task

from .models import Channel
from .services import provision_channel

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=5)
def provision_live_input_task(self, channel_id: int) -> None:  # noqa: ARG001
    """Provisioning async (conservé pour usage worker ; l'approbation provisionne
    de façon synchrone — cf. streamers.services)."""
    channel = Channel.objects.filter(pk=channel_id).first()
    if channel is None:
        logger.warning("provision_live_input_task: channel %s introuvable", channel_id)
        return
    provision_channel(channel)
