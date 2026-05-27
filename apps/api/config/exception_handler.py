"""Handler d'exceptions DRF : enveloppe d'erreur homogène.

Conserve `detail` quand il existe (compat front), et enveloppe les erreurs de
validation par champ sous `{detail, errors}`.
"""

from __future__ import annotations

from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None
    data = response.data
    if isinstance(data, list) or (isinstance(data, dict) and "detail" not in data):
        response.data = {"detail": "Requête invalide.", "errors": data}
    return response
