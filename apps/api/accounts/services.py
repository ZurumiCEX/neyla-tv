"""Logique métier de l'auth : aucun import DRF ici, juste Django + nos modules."""

from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone

from .models import RESERVED_USERNAMES, User
from .tokens import (
    EMAIL_VERIFY_PURPOSE,
    EMAIL_VERIFY_TTL,
    PASSWORD_RESET_PURPOSE,
    PASSWORD_RESET_TTL,
    InvalidToken,
    read_token,
)


class RegistrationError(Exception):
    """Données d'inscription invalides (collision, username réservé, etc.)."""


@transaction.atomic
def register_user(*, email: str, username: str, password: str) -> User:
    """Crée un utilisateur. Lève RegistrationError si conflit ou règle violée."""
    username_lc = username.lower()
    if username_lc in RESERVED_USERNAMES:
        raise RegistrationError("Ce username est réservé.")
    if User.objects.filter(email__iexact=email).exists():
        raise RegistrationError("Un compte existe déjà avec cet email.")
    if User.objects.filter(username=username_lc).exists():
        raise RegistrationError("Ce username est déjà pris.")
    validate_password(password)
    return User.objects.create_user(email=email, username=username_lc, password=password)


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
    return user


@transaction.atomic
def reset_password_with_token(token: str, new_password: str) -> User:
    try:
        user_id = read_token(token, PASSWORD_RESET_PURPOSE, PASSWORD_RESET_TTL)
    except InvalidToken:
        raise
    user = User.objects.select_for_update().filter(pk=user_id).first()
    if user is None:
        raise InvalidToken("Utilisateur introuvable.")
    validate_password(new_password, user=user)
    user.set_password(new_password)
    user.save(update_fields=["password"])
    return user
