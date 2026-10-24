"""E-mails de sécurité : nouvel appareil, 2FA, passkeys, mot de passe.

Best-effort : un échec d'envoi n'interrompt jamais l'action de l'utilisateur.
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

MESSAGES = {
    "new_login": (
        "Nouvelle connexion à ton compte Neyla TV",
        "Une connexion a eu lieu depuis un nouvel appareil : {detail}.\n\n"
        "Si ce n'est pas toi, change ton mot de passe et déconnecte les autres appareils "
        "depuis Paramètres → Sécurité : {url}/settings",
    ),
    "password_changed": (
        "Ton mot de passe Neyla TV a été modifié",
        "Le mot de passe de ton compte vient d'être changé ; les autres appareils ont été "
        "déconnectés.\n\nSi ce n'est pas toi, réinitialise-le tout de suite : "
        "{url}/forgot-password",
    ),
    "2fa_enabled": (
        "Double authentification activée",
        "La double authentification (2FA) est maintenant active sur ton compte Neyla TV.",
    ),
    "2fa_disabled": (
        "Double authentification désactivée",
        "La double authentification (2FA) a été désactivée sur ton compte Neyla TV.\n\n"
        "Si ce n'est pas toi, sécurise ton compte : {url}/settings",
    ),
    "passkey_added": (
        "Nouvelle passkey ajoutée",
        "Une passkey « {detail} » a été ajoutée à ton compte Neyla TV.\n\n"
        "Si ce n'est pas toi, supprime-la depuis Paramètres → Sécurité : {url}/settings",
    ),
    "passkey_removed": (
        "Passkey supprimée",
        "La passkey « {detail} » a été retirée de ton compte Neyla TV.",
    ),
}


def notify(user, kind: str, detail: str = "") -> None:
    subject, body = MESSAGES[kind]
    if not getattr(user, "email", ""):
        return
    try:
        send_mail(
            subject=subject,
            message=body.format(detail=detail or "—", url=settings.FRONTEND_URL),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception:  # noqa: BLE001
        logger.warning("e-mail de sécurité %s non envoyé (user %s)", kind, user.pk)
