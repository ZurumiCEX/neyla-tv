"""Réponse immédiate à /api/livez, avant toute validation d'hôte.

Le health check de Fly.io (et des PaaS en général) appelle la machine par son
IP interne : sans ce raccourci, ALLOWED_HOSTS le rejetterait (400) et la
plateforme considérerait l'app comme morte.
"""

from __future__ import annotations

from django.http import JsonResponse


class LivenessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "GET" and request.path_info == "/api/livez":
            return JsonResponse({"status": "ok"})
        return self.get_response(request)
