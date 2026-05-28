"""Tâches Celery des abonnements (renouvellement/expiration via beat)."""

from __future__ import annotations

from celery import shared_task

from . import services


@shared_task(name="subscriptions.tasks.process_due_subscriptions_task")
def process_due_subscriptions_task() -> dict:
    """Renouvelle/expire les abonnements échus. Planifié par Celery beat."""
    return services.process_due_subscriptions()
