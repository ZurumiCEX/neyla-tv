"""Tests de l'ajustement manuel de solde Aura (back-office admin)."""

from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User
from audit.models import AuditEvent
from payments import services
from payments.models import LedgerEntry, Wallet

pytestmark = pytest.mark.django_db


def test_adjust_balance_credit_and_audit():
    actor = UserFactory(role=User.Role.ADMIN)
    user = UserFactory()
    wallet = services.adjust_balance(actor, user, 500, "bonus support")
    assert wallet.aura_balance == 500
    entry = LedgerEntry.objects.get(wallet=wallet)
    assert entry.kind == LedgerEntry.Kind.ADJUSTMENT
    assert entry.amount == 500
    assert AuditEvent.objects.filter(action="wallet.adjust").exists()


def test_adjust_balance_debit():
    actor = UserFactory(role=User.Role.ADMIN)
    user = UserFactory()
    services.adjust_balance(actor, user, 800, "crédit initial")
    wallet = services.adjust_balance(actor, user, -300, "correction")
    assert wallet.aura_balance == 500


def test_adjust_balance_rejects_negative_result():
    actor = UserFactory(role=User.Role.ADMIN)
    user = UserFactory()
    with pytest.raises(services.InsufficientBalanceError):
        services.adjust_balance(actor, user, -50, "trop")


def test_adjust_balance_rejects_zero():
    actor = UserFactory(role=User.Role.ADMIN)
    user = UserFactory()
    with pytest.raises(services.PaymentError):
        services.adjust_balance(actor, user, 0, "rien")


def test_admin_action_applies_adjustment():
    boss = User.objects.create_superuser(
        username="boss", email="boss@example.com", password="pw-12345"
    )
    user = UserFactory()
    wallet, _ = Wallet.objects.get_or_create(user=user)
    client = Client()
    client.force_login(boss)
    resp = client.post(
        reverse("admin:payments_wallet_changelist"),
        {
            "action": "adjust_aura",
            "apply": "1",
            "_selected_action": [wallet.pk],
            "amount": "250",
            "reason": "compensation incident",
        },
        follow=True,
    )
    assert resp.status_code == 200
    wallet.refresh_from_db()
    assert wallet.aura_balance == 250
