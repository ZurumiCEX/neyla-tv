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


def _timed(check_fn):
    """Renvoie ``{ok, latency_ms}`` pour une fonction de check booléenne."""
    import time

    start = time.perf_counter()
    ok = False
    try:
        ok = bool(check_fn())
    except Exception:
        ok = False
    return {"ok": ok, "latency_ms": int((time.perf_counter() - start) * 1000)}


def _check_cloudflare_stream() -> bool:
    """Best-effort : OK si client FAKE (offline) ou clé API présente."""
    token = getattr(settings, "CLOUDFLARE_API_TOKEN", "") or ""
    if not token:
        return True  # mode FAKE → considéré « OK » (pas d'appel réseau).
    try:
        import urllib.request

        req = urllib.request.Request(
            "https://api.cloudflare.com/client/v4/user/tokens/verify",
            headers={"Authorization": f"Bearer {token}"},
        )
        with urllib.request.urlopen(req, timeout=3) as r:  # noqa: S310 - URL fixe
            return 200 <= r.status < 500
    except Exception:
        return False


@api_view(["GET"])
@permission_classes([AllowAny])
def status_overview(_request) -> JsonResponse:
    """État détaillé pour la page publique `/statut` (services + latences)."""
    from django.utils import timezone

    services = {
        "database": _timed(_check_db),
        "redis": _timed(_check_redis),
        "cloudflare_stream": _timed(_check_cloudflare_stream),
        "api": {"ok": True, "latency_ms": 0},
    }
    all_ok = all(s["ok"] for s in services.values())
    return JsonResponse(
        {
            "status": "ok" if all_ok else "degraded",
            "services": services,
            "checked_at": timezone.now().isoformat(),
            "uptime_pct_30d": None,  # à brancher quand HealthCheck sera collecté.
            "incidents": [],
        }
    )
