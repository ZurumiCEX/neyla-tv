"""Conftest racine : config Celery eager + backend mail locmem pour les tests."""

from __future__ import annotations


def pytest_configure(config):
    from django.conf import settings

    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    # On désactive le rate-limit en tests pour ne pas casser les itérations.
    settings.RATELIMIT_ENABLE = False
