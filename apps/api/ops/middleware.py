"""Middleware mode maintenance : 503 sauf staff et IPs allow-listées.

- Pour `/api/*` : retourne 503 JSON `{detail, retry_after_minutes?}`.
- Pour le reste : rend la template `maintenance.html`.
- Préserve `/admin/`, `/django-static/`, `/static/` et le endpoint santé.
"""

from __future__ import annotations

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render

# Chemins toujours autorisés (admin, santé, statiques).
_BYPASS_PREFIXES = (
    "/admin/",
    "/django-static/",
    "/static/",
    "/api/healthz",
    "/api/livez",
    "/api/status",
)


def _client_ip(request) -> str:
    """Best-effort : récupère l'IP du client (X-Forwarded-For en prod derrière proxy)."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def _allowed(request) -> bool:
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_staff", False):
        return True
    allow = getattr(settings, "MAINTENANCE_ALLOWED_IPS", []) or []
    return _client_ip(request) in set(allow)


class MaintenanceModeMiddleware:
    """Bloque les requêtes pendant la maintenance, sauf staff / IPs allow-listées."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or "/"
        if any(path.startswith(p) for p in _BYPASS_PREFIXES):
            return self.get_response(request)

        # Lazy import (l'app peut ne pas être prête au boot Django strict).
        try:
            from .models import maintenance_state
        except Exception:  # pragma: no cover - fail-open
            return self.get_response(request)

        state = maintenance_state()
        if not state["active"]:
            return self.get_response(request)
        if _allowed(request):
            return self.get_response(request)

        message = state["message"] or "Le site est en maintenance. Merci de revenir plus tard."
        if path.startswith("/api/"):
            return JsonResponse({"detail": message, "maintenance": True}, status=503)
        return render(request, "ops/maintenance.html", {"message": message}, status=503)
