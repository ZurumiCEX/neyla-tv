"""Logique métier de l'auth : aucun import DRF ici, juste Django + nos modules."""

from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from .models import RESERVED_USERNAMES, User
from .tokens import (
    EMAIL_VERIFY_PURPOSE,
    EMAIL_VERIFY_TTL,
    InvalidToken,
    read_token,
)


class RegistrationError(Exception):
    """Données d'inscription invalides (collision, username réservé, etc.)."""


@transaction.atomic
def register_user(
    *,
    email: str,
    username: str,
    password: str,
    invite_code: str = "",
    terms_accepted: bool = False,
    date_of_birth=None,
) -> User:
    """Crée un utilisateur. Lève RegistrationError si conflit ou règle violée."""
    if not terms_accepted:
        raise RegistrationError(
            "Vous devez attester avoir 18 ans ou plus et accepter les conditions d'utilisation."
        )
    username_lc = username.lower()
    if username_lc in RESERVED_USERNAMES:
        raise RegistrationError("Ce username est réservé.")
    if User.objects.filter(email__iexact=email).exists():
        raise RegistrationError("Un compte existe déjà avec cet email.")
    if User.objects.filter(username=username_lc).exists():
        raise RegistrationError("Ce username est déjà pris.")
    # Utilisateur provisoire : active le contrôle de similarité mot de passe /
    # email / username (sans lui, le validateur ne compare rien).
    validate_password(password, user=User(email=email, username=username_lc))
    user = User.objects.create_user(email=email, username=username_lc, password=password)
    user.terms_accepted_at = timezone.now()
    user.date_of_birth = date_of_birth
    user.save(update_fields=["terms_accepted_at", "date_of_birth"])
    if invite_code:
        from invitations.services import try_redeem

        try_redeem(invite_code, user)
    return user


def verify_email_token(token: str) -> User:
    """Marque l'email comme vérifié. Idempotent : ré-appeler ne casse rien."""
    try:
        user_id = read_token(token, EMAIL_VERIFY_PURPOSE, EMAIL_VERIFY_TTL)
    except InvalidToken:
        raise
    user = User.objects.filter(pk=user_id).first()
    if user is None:
        raise InvalidToken("Utilisateur introuvable.")
    if not user.is_email_verified:
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified_at"])
        import contextlib

        with contextlib.suppress(Exception):
            from invitations.services import reward_for_verified

            reward_for_verified(user)
    return user


@transaction.atomic
def reset_password_with_token(token: str, new_password: str) -> User:
    """Nouveau mot de passe via le lien e-mail (usage unique), puis déconnexion partout."""
    from .tokens import read_reset_token

    user = read_reset_token(
        token, lambda pk: User.objects.select_for_update().filter(pk=int(pk)).first()
    )
    validate_password(new_password, user=user)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    from . import security, sessions

    sessions.revoke_all(user)
    transaction.on_commit(lambda: security.notify(user, "password_changed"))
    return user
