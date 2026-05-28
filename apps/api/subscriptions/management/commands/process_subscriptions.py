"""Renouvelle/expire les abonnements échus.

    python manage.py process_subscriptions

À planifier (cron ou Celery beat) ; idempotent et exécutable à la main.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from subscriptions import services


class Command(BaseCommand):
    help = "Renouvelle (débit Aura) ou expire les abonnements arrivés à échéance."

    def handle(self, *args, **options):
        result = services.process_due_subscriptions()
        self.stdout.write(
            self.style.SUCCESS(
                f"Abonnements traités : {result['renewed']} renouvelé(s), "
                f"{result['expired']} expiré(s)."
            )
        )
