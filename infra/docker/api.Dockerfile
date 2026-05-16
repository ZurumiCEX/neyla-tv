# Image Django API — multi-stage : dev (par défaut) ou prod.
ARG PYTHON_VERSION=3.12-slim

# --- base : deps système + requirements communs ---
FROM python:${PYTHON_VERSION} AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
 && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements/ /app/requirements/

# --- dev : pytest + linters, code monté en volume ---
FROM base AS dev
RUN pip install -r /app/requirements/dev.txt
COPY apps/api/ /app/
EXPOSE 8000
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]

# --- prod : runtime minimaliste, settings prod, user non-root ---
FROM base AS prod
RUN pip install -r /app/requirements/prod.txt \
 && groupadd -r django && useradd -r -g django django
COPY apps/api/ /app/
RUN chown -R django:django /app
USER django
ENV DJANGO_SETTINGS_MODULE=config.settings.prod
EXPOSE 8000
# Daphne pour servir HTTP+WS (Channels). On a besoin d'ASGI.
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "--access-log", "-", "config.asgi:application"]
