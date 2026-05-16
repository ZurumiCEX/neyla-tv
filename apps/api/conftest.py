"""Conftest racine : config Celery eager + backend mail locmem + channel layer in-memory."""

from __future__ import annotations


def pytest_configure(config):  # noqa: ARG001
    from django.conf import settings

    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    settings.RATELIMIT_ENABLE = False
    # Pour les tests WebSocket : pas besoin de Redis pubsub, in-memory suffit.
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"},
    }
