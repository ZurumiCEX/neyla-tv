"""Tests parrainage : récompenses Aura de base + paliers + stats (gated email)."""

from __future__ import annotations

import pytest
from django.utils import timezone

from accounts.factories import UserFactory
from accounts.services import verify_email_token
from accounts.tokens import EMAIL_VERIFY_PURPOSE, make_token
from invitations import services
from payments.services import get_wallet

pytestmark = pytest.mark.django_db


def _verify(user) -> None:
    """Helper : simule la vérification de l'email du filleul (ordre = service réel)."""
    user.email_verified_at = timezone.now()
    user.save(update_fields=["email_verified_at"])
    services.reward_for_verified(user)


def test_redeem_alone_does_not_reward_inviter():
    """Avant vérification de l'email, aucune Aura n'est versée."""
    inviter = UserFactory()
    invite = services.create_invite(inviter, max_uses=10)
    filleul = UserFactory(email_verified_at=None)
    services.redeem(invite.code, filleul)
    assert get_wallet(inviter).aura_balance == 0
    assert services.successful_count(inviter) == 0  # email non vérifié


def test_referral_grants_base_aura_after_email_verified():
    inviter = UserFactory()
    invite = services.create_invite(inviter, max_uses=10)
    filleul = UserFactory(email_verified_at=None)
    services.redeem(invite.code, filleul)
    _verify(filleul)
    assert get_wallet(inviter).aura_balance == services.REFERRAL_BASE_REWARD
    assert services.successful_count(inviter) == 1


def test_referral_tier_bonus_at_threshold_after_verifications():
    inviter = UserFactory()
    invite = services.create_invite(inviter, max_uses=100)
    filleuls = [UserFactory(email_verified_at=None) for _ in range(5)]
    for f in filleuls:
        services.redeem(invite.code, f)
    for f in filleuls:
        _verify(f)
    # 5 filleuls validés : 5*base + bonus palier "silver" (200).
    expected = services.REFERRAL_BASE_REWARD * 5 + 200
    assert get_wallet(inviter).aura_balance == expected


def test_referral_stats_shape():
    inviter = UserFactory()
    invite = services.create_invite(inviter, max_uses=10)
    filleul = UserFactory(email_verified_at=None)
    services.redeem(invite.code, filleul)
    _verify(filleul)
    stats = services.referral_stats(inviter)
    assert stats["successful_invites"] == 1
    assert stats["aura_earned"] == services.REFERRAL_BASE_REWARD
    assert stats["current_tier"] == "bronze"


def test_verify_email_token_grants_referral_once():
    """Le flux complet via verify_email_token verse la récompense une seule fois."""
    inviter = UserFactory()
    invite = services.create_invite(inviter, max_uses=5)
    filleul = UserFactory(email_verified_at=None)
    services.redeem(invite.code, filleul)
    token = make_token(filleul.pk, EMAIL_VERIFY_PURPOSE)
    verify_email_token(token)  # première vérification → récompense
    verify_email_token(token)  # idempotent → pas de double récompense
    assert get_wallet(inviter).aura_balance == services.REFERRAL_BASE_REWARD
