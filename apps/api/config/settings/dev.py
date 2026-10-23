"""Settings de développement : DEBUG, hosts permissifs."""

from .base import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["*"]
# Dev : providers de paiement simulés autorisés (Aura créditée sans encaissement).
PAYMENTS_ALLOW_FAKE = True
