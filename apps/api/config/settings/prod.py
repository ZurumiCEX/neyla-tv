"""Settings de production : DEBUG off, headers sécurité, Sentry, logs JSON."""

from __future__ import annotations

import json
import logging

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False
# default=[] : permet le `collectstatic` au build de l'image (aucun host
# requis), tout en restant fail-closed au runtime si la variable est absente.
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# Origines de confiance pour le CSRF (admin Django derrière HTTPS).
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# WhiteNoise : compression + manifest hashé. Servi sous /django-static/ pour
# ne pas entrer en collision avec les assets Next.js (/_next/...).
STATIC_URL = "/django-static/"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Cloudflare termine TLS et nous parle en HTTP, mais ajoute X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Le refresh cookie passe par HTTPS en prod.
REFRESH_COOKIE_SECURE = True


# --- Logging JSON ---
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            payload["exc_type"] = record.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": "config.settings.prod.JsonFormatter"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "json"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# --- Sentry (best-effort : si DSN non configuré, on skip silencieusement) ---
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
        traces_sample_rate=float(env("SENTRY_TRACES_SAMPLE_RATE", default="0.1")),
        send_default_pii=False,
        environment=env("SENTRY_ENVIRONMENT", default="prod"),
    )
