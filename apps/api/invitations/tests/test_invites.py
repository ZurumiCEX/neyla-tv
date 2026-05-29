"""Tests parrainage : récompenses Aura de base + paliers + stats."""

from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from invitations import services
from payments.services import get_wallet

pytestmark = pytest.mark.django_db


def test_referral_grants_base_aura():
    inviter = UserFactory()
    invite = services.create_invite(inviter, max_uses=10)
    services.redeem(invite.code, UserFactory())
    assert get_wallet(inviter).aura_balance == services.REFERRAL_BASE_REWARD


def test_referral_tier_bonus_at_threshold():
    inviter = UserFactory()
    invite = services.create_invite(inviter, max_uses=100)
    for _ in range(5):
        services.redeem(invite.code, UserFactory())
    # 5 filleuls : 5*base + bonus palier "silver" (200).
    expected = services.REFERRAL_BASE_REWARD * 5 + 200
    assert get_wallet(inviter).aura_balance == expected


def test_referral_stats_shape():
    inviter = UserFactory()
    invite = services.create_invite(inviter, max_uses=10)
    services.redeem(invite.code, UserFactory())
    stats = services.referral_stats(inviter)
    assert stats["successful_invites"] == 1
    assert stats["aura_earned"] == services.REFERRAL_BASE_REWARD
    assert stats["current_tier"] == "bronze"
