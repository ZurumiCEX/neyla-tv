"""Bootstrap Celery : lit les settings Django, autodiscover des tâches."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("neyla")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def ping(self) -> str:
    """Tâche factice pour valider le worker en Phase 0."""
    return "pong"
