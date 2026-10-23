"""Handler d'exceptions DRF : enveloppe d'erreur homogène.

Conserve `detail` quand il existe (compat front), et enveloppe les erreurs de
validation par champ sous `{detail, errors}`. `detail` reprend alors le premier
message de champ, pour que le front affiche la vraie raison (et non un texte
générique).
"""

from __future__ import annotations

from rest_framework.views import exception_handler as drf_exception_handler

RATE_LIMITED_DETAIL = "Trop de tentatives, réessaie dans quelques minutes."


def exception_handler(exc, context):
    from django_ratelimit.exceptions import Ratelimited
    from rest_framework.response import Response

    # django-ratelimit lève un PermissionDenied (→ 403 « permission refusée ») :
    # on renvoie un vrai 429 avec un message compréhensible.
    if isinstance(exc, Ratelimited):
        return Response({"detail": RATE_LIMITED_DETAIL}, status=429)
    response = drf_exception_handler(exc, context)
    if response is None:
        return None
    data = response.data
    if isinstance(data, list) or (isinstance(data, dict) and "detail" not in data):
        response.data = {"detail": _first_message(data) or "Requête invalide.", "errors": data}
    return response


def _first_message(data) -> str:
    """Premier message lisible d'une structure d'erreurs DRF (dict / list imbriqués)."""
    if isinstance(data, dict):
        for value in data.values():
            msg = _first_message(value)
            if msg:
                return msg
        return ""
    if isinstance(data, list):
        for value in data:
            msg = _first_message(value)
            if msg:
                return msg
        return ""
    return str(data)
