"""Settings de développement : DEBUG, hosts permissifs."""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
# Dev : providers de paiement simulés autorisés (Aura créditée sans encaissement).
PAYMENTS_ALLOW_FAKE = True
# Dev en HTTP : un cookie « Secure » ne serait pas renvoyé → session perdue
# au rechargement (base.py calcule ce réglage avant que DEBUG passe à True).
REFRESH_COOKIE_SECURE = False
