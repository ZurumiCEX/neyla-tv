"""Tokens signés à courte durée de vie pour vérif email et reset password.

On utilise `TimestampSigner` de Django : pas besoin de stocker un état en base,
le token contient l'user_id + un purpose, signé avec SECRET_KEY.
Le purpose empêche de réutiliser un token email-verify comme password-reset.
"""

from __future__ import annotations

from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

EMAIL_VERIFY_PURPOSE = "email-verify"
EMAIL_VERIFY_TTL = 60 * 60 * 24  # 24h

PASSWORD_RESET_PURPOSE = "password-reset"  # noqa: S105 (purpose, pas un secret)
PASSWORD_RESET_TTL = 60 * 60  # 1h

TWO_FACTOR_PURPOSE = "two-factor-login"  # noqa: S105 (purpose, pas un secret)
TWO_FACTOR_TTL = 60 * 5  # 5 min pour saisir le code


class InvalidTokenError(Exception):
    """Token absent, mal signé, ou expiré."""


# Alias de compat pour ne pas casser les imports historiques.
InvalidToken = InvalidTokenError


def _password_fingerprint(user) -> str:
    import hashlib

    return hashlib.sha256(f"{user.pk}:{user.password}".encode()).hexdigest()[:16]


def make_reset_token(user) -> str:
    """Token de réinitialisation lié au mot de passe actuel : inutilisable une fois changé."""
    return TimestampSigner(salt=PASSWORD_RESET_PURPOSE).sign(
        f"{user.pk}:{_password_fingerprint(user)}"
    )


def read_reset_token(token: str, user_loader) -> object:
    """Renvoie l'utilisateur si le token est valide et le mot de passe inchangé."""
    try:
        payload = TimestampSigner(salt=PASSWORD_RESET_PURPOSE).unsign(
            token, max_age=PASSWORD_RESET_TTL
        )
    except SignatureExpired as exc:
        raise InvalidTokenError("Token expiré.") from exc
    except BadSignature as exc:
        raise InvalidTokenError("Token invalide.") from exc
    user_id, _, fingerprint = payload.partition(":")
    user = user_loader(user_id) if user_id.isdigit() else None
    if user is None or not fingerprint or fingerprint != _password_fingerprint(user):
        raise InvalidTokenError("Lien déjà utilisé ou expiré.")
    return user


def make_token(user_id: int, purpose: str) -> str:
    return TimestampSigner(salt=purpose).sign(str(user_id))


def read_token(token: str, purpose: str, max_age: int) -> int:
    try:
        payload = TimestampSigner(salt=purpose).unsign(token, max_age=max_age)
    except SignatureExpired as exc:
        raise InvalidTokenError("Token expiré.") from exc
    except BadSignature as exc:
        raise InvalidTokenError("Token invalide.") from exc
    try:
        return int(payload)
    except ValueError as exc:
        raise InvalidTokenError("Payload illisible.") from exc
