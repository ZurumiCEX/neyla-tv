"""Tests du tableau de bord intégré à la page d'accueil du Django admin."""

from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User
from analytics.services import admin_dashboard_metrics
from channels_app.models import Channel
from payments.models import Wallet

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff_client():
    boss = User.objects.create_superuser(
        username="boss", email="boss@example.com", password="pw-12345"
    )
    client = Client()
    client.force_login(boss)
    return client


def test_admin_dashboard_metrics_shape():
    m = admin_dashboard_metrics(30)
    assert set(m) >= {"overview", "growth", "revenue", "new_users_series", "moderation"}
    assert len(m["new_users_series"]) == 30
    assert {"open_reports", "pending_flags", "open_risk", "pending_payouts"} <= set(m["moderation"])
    assert "series" in m["revenue"] and "totals" in m["revenue"]


def test_admin_index_renders_dashboard_for_staff(staff_client):
    resp = staff_client.get(reverse("admin:index"))
    assert resp.status_code == 200
    html = resp.content.decode()
    # KPIs + graphiques SVG rendus dans la page d'accueil
    assert "Suivi de l'activité" in html
    assert "neyla-kpi" in html
    assert "<svg" in html


def test_channel_change_page_shows_session_inline(staff_client):
    channel = Channel.objects.get(user=UserFactory())
    resp = staff_client.get(reverse("admin:channels_app_channel_change", args=[channel.pk]))
    assert resp.status_code == 200
    assert "Sessions récentes" in resp.content.decode()


def test_wallet_change_page_shows_ledger_inline(staff_client):
    wallet, _ = Wallet.objects.get_or_create(user=UserFactory())
    resp = staff_client.get(reverse("admin:payments_wallet_change", args=[wallet.pk]))
    assert resp.status_code == 200
    assert "Mouvements" in resp.content.decode()


def test_user_change_page_shows_session_inline(staff_client):
    user = UserFactory()
    resp = staff_client.get(reverse("admin:accounts_user_change", args=[user.pk]))
    assert resp.status_code == 200
    assert "Sessions / appareils" in resp.content.decode()
