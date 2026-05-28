"""Services invitations : génération de code, redemption à l'inscription, compteur."""

from __future__ import annotations

import secrets

from django.db import transaction

from .models import Invite

_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sans I/O/0/1 ambigus
_CODE_LEN = 8


class InviteError(Exception):
    """Code invalide, expiré ou épuisé."""


def _generate_code() -> str:
    for _ in range(10):
        code = "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LEN))
        if not Invite.objects.filter(code=code).exists():
            return code
    raise InviteError("Impossible de générer un code unique.")


def create_invite(inviter, max_uses: int = 1, expires_at=None) -> Invite:
    return Invite.objects.create(
        code=_generate_code(),
        inviter=inviter,
        max_uses=max(1, int(max_uses)),
        expires_at=expires_at,
    )


@transaction.atomic
def redeem(code: str, new_user) -> Invite:
    """Lie `new_user.invited_by` à l'inviteur et incrémente le compteur. Lève si invalide."""
    invite = Invite.objects.select_for_update().filter(code=(code or "").strip().upper()).first()
    if invite is None or not invite.is_usable:
        raise InviteError("Code d'invitation invalide ou expiré.")
    if invite.inviter_id == new_user.id:
        raise InviteError("Tu ne peux pas utiliser ton propre code.")
    invite.used_count += 1
    invite.save(update_fields=["used_count"])
    new_user.invited_by = invite.inviter
    new_user.save(update_fields=["invited_by"])
    return invite


def try_redeem(code: str, new_user) -> Invite | None:
    """Variante silencieuse pour l'inscription : ignore les codes invalides."""
    if not code:
        return None
    try:
        return redeem(code, new_user)
    except InviteError:
        return None


def successful_count(user) -> int:
    from accounts.models import User

    return User.objects.filter(invited_by=user).count()
