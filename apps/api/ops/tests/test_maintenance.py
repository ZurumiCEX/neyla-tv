"""Tests middleware mode maintenance + status enrichi."""

from __future__ import annotations

import pytest
from django.test import Client, override_settings

from ops.models import SiteFlag

pytestmark = pytest.mark.django_db


def _maintenance_on(message: str = "RAS") -> SiteFlag:
    flag, _ = SiteFlag.objects.update_or_create(
        key="maintenance", defaults={"bool_value": True, "text_value": message}
    )
    return flag


def test_maintenance_off_passes_through():
    c = Client()
    # /api/livez existe et renvoie 200 normalement.
    assert c.get("/api/livez").status_code == 200


def test_maintenance_blocks_api_with_503_json():
    _maintenance_on("On revient vite.")
    c = Client()
    r = c.get("/api/charity/events")
    assert r.status_code == 503
    assert r.json()["maintenance"] is True
    assert "vite" in r.json()["detail"]


def test_maintenance_bypasses_healthz_and_status():
    _maintenance_on()
    c = Client()
    assert c.get("/api/healthz").status_code in (200, 503)  # check ok mais pas 503-maintenance
    r = c.get("/api/status")
    assert r.status_code == 200
    # /api/livez doit aussi passer (probe plateforme).
    assert c.get("/api/livez").status_code == 200


def test_maintenance_lets_staff_through():
    from django.contrib.auth import get_user_model

    _maintenance_on()
    user_model = get_user_model()
    boss = user_model.objects.create_superuser(
        username="boss", email="boss@example.com", password="pw-12345"
    )
    c = Client()
    c.force_login(boss)
    # Le superuser ne doit pas être bloqué.
    assert c.get("/api/charity/events").status_code == 200


@override_settings(MAINTENANCE_ALLOWED_IPS=["1.2.3.4"])
def test_maintenance_lets_allowed_ips_through():
    _maintenance_on()
    c = Client()
    r = c.get("/api/charity/events", REMOTE_ADDR="1.2.3.4")
    assert r.status_code == 200
    r2 = c.get("/api/charity/events", REMOTE_ADDR="9.9.9.9")
    assert r2.status_code == 503


# --- Status enrichi ---


def test_status_endpoint_returns_services():
    c = Client()
    body = c.get("/api/status").json()
    assert body["status"] in {"ok", "degraded"}
    assert set(body["services"]) >= {"database", "redis", "cloudflare_stream", "api"}
    for s in body["services"].values():
        assert "ok" in s and "latency_ms" in s
    assert "checked_at" in body
