"""Tests du tableau de bord intégré à la page d'accueil du Django admin."""

from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import User
from analytics.services import admin_dashboard_metrics

pytestmark = pytest.mark.django_db


def test_admin_dashboard_metrics_shape():
    m = admin_dashboard_metrics(30)
    assert set(m) >= {"overview", "growth", "revenue", "new_users_series", "moderation"}
    assert len(m["new_users_series"]) == 30
    assert {"open_reports", "pending_flags", "open_risk", "pending_payouts"} <= set(m["moderation"])
    assert "series" in m["revenue"] and "totals" in m["revenue"]


def test_admin_index_renders_dashboard_for_staff():
    boss = User.objects.create_superuser(
        username="boss", email="boss@example.com", password="pw-12345"
    )
    client = Client()
    client.force_login(boss)
    resp = client.get(reverse("admin:index"))
    assert resp.status_code == 200
    html = resp.content.decode()
    # KPIs + graphiques SVG rendus dans la page d'accueil
    assert "Suivi de l'activité" in html
    assert "neyla-kpi" in html
    assert "<svg" in html
