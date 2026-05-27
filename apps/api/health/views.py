"""Healthcheck : ping Postgres + Redis. Renvoie 200 si tout est OK, 503 sinon."""

from __future__ import annotations

import redis
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def livez(_request) -> JsonResponse:
    """Liveness : 200 si le process répond. Aucune dépendance (DB/Redis).

    Utilisé comme health check de la plateforme (PaaS) : un incident Redis ou DB
    ne doit pas faire échouer le déploiement ni redémarrer le conteneur en boucle.
    La santé des dépendances est exposée par /api/healthz (readiness/monitoring).
    """
    return JsonResponse({"status": "ok"})


def _check_db() -> bool:
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except Exception:
        return False


def _check_redis() -> bool:
    try:
        client = redis.Redis.from_url(
            settings.REDIS_URL, socket_connect_timeout=3, socket_timeout=3
        )
        return bool(client.ping())
    except Exception:
        return False


@api_view(["GET"])
@permission_classes([AllowAny])
def healthz(_request) -> JsonResponse:
    db_ok = _check_db()
    redis_ok = _check_redis()
    status_ok = db_ok and redis_ok
    return JsonResponse(
        {
            "status": "ok" if status_ok else "degraded",
            "db": db_ok,
            "redis": redis_ok,
        },
        status=200 if status_ok else 503,
    )
