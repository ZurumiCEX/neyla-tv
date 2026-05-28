"""Bootstrap Celery : lit les settings Django, autodiscover des tâches."""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("neyla")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Planification lue par `celery beat` : renouvellement quotidien des abonnements.
app.conf.beat_schedule = {
    "process-due-subscriptions": {
        "task": "subscriptions.tasks.process_due_subscriptions_task",
        "schedule": crontab(hour=3, minute=0),
    },
}


@app.task(bind=True)
def ping(self) -> str:
    """Tâche factice pour valider le worker en Phase 0."""
    return "pong"
