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
    """Lie `new_user.invited_by` à l'inviteur et incrémente le compteur. Lève si invalide.

    NB : la récompense Aura n'est PAS versée ici. Elle l'est uniquement quand le
    filleul valide son email (anti-abus) via ``reward_for_verified``.
    """
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
    """Filleuls **validés** : compte les inscrits ayant vérifié leur email."""
    from accounts.models import User

    return User.objects.filter(invited_by=user, email_verified_at__isnull=False).count()


def reward_for_verified(user) -> None:
    """Verse la récompense de parrainage quand le filleul valide son email.

    Idempotent au niveau de l'appel : ``verify_email_token`` ne nous appelle
    qu'à la première vérification (``if not user.is_email_verified``), donc
    la récompense est versée exactement une fois.
    """
    inviter_id = getattr(user, "invited_by_id", None)
    if not inviter_id:
        return
    from accounts.models import User

    inviter = User.objects.filter(pk=inviter_id).first()
    if inviter is None:
        return
    import contextlib

    with contextlib.suppress(Exception):
        reward_referral(inviter, user)


# --- Parrainage : récompenses en Aura par palier ----------------------------

# Aura crédités à chaque filleul inscrit.
REFERRAL_BASE_REWARD = 50
# Bonus de palier accordés une seule fois quand le nombre de filleuls atteint le seuil.
REFERRAL_TIERS = [
    {"threshold": 1, "bonus": 0, "key": "bronze"},
    {"threshold": 5, "bonus": 200, "key": "silver"},
    {"threshold": 10, "bonus": 500, "key": "gold"},
    {"threshold": 25, "bonus": 1500, "key": "platinum"},
    {"threshold": 50, "bonus": 5000, "key": "diamond"},
]


def _grant(user, amount: int, reference: str) -> None:
    if amount <= 0:
        return
    from payments.models import LedgerEntry
    from payments.services import grant_aura

    grant_aura(user, amount, LedgerEntry.Kind.REFERRAL, reference)


def reward_referral(inviter, new_user) -> None:
    """Récompense l'inviteur : Aura de base + bonus si un palier est atteint."""
    count = successful_count(inviter)
    _grant(inviter, REFERRAL_BASE_REWARD, f"referral:{new_user.username}")
    for tier in REFERRAL_TIERS:
        if count == tier["threshold"] and tier["bonus"] > 0:
            _grant(inviter, tier["bonus"], f"referral-tier:{tier['key']}")


def referral_tier(count: int) -> dict | None:
    current = None
    for tier in REFERRAL_TIERS:
        if count >= tier["threshold"]:
            current = tier
    return current


def next_referral_tier(count: int) -> dict | None:
    return next((t for t in REFERRAL_TIERS if count < t["threshold"]), None)


def referral_stats(user) -> dict:
    from django.db.models import Sum

    from payments.models import LedgerEntry

    count = successful_count(user)
    earned = (
        LedgerEntry.objects.filter(wallet__user=user, kind=LedgerEntry.Kind.REFERRAL).aggregate(
            s=Sum("amount")
        )["s"]
        or 0
    )
    current = referral_tier(count)
    nxt = next_referral_tier(count)
    return {
        "successful_invites": count,
        "aura_earned": int(earned),
        "base_reward": REFERRAL_BASE_REWARD,
        "current_tier": current["key"] if current else None,
        "next_tier": nxt,
        "tiers": REFERRAL_TIERS,
    }
