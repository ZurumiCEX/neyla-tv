"""IP réelle derrière proxy + limites de débit + message 429."""

from __future__ import annotations

import pytest
from django.test import RequestFactory
from django.urls import reverse

from config.client_ip import client_ip

pytestmark = pytest.mark.django_db


def _req(**meta):
    return RequestFactory().get("/", **meta)


def test_client_ip_header_precedence():
    assert client_ip(_req(REMOTE_ADDR="10.0.0.1")) == "10.0.0.1"
    assert client_ip(_req(REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="41.82.1.2, 10.0.0.1")) == (
        "41.82.1.2"
    )
    assert (
        client_ip(
            _req(
                REMOTE_ADDR="10.0.0.1",
                HTTP_X_FORWARDED_FOR="41.82.1.2",
                HTTP_DO_CONNECTING_IP="196.207.3.4",
            )
        )
        == "196.207.3.4"
    )
    assert (
        client_ip(_req(HTTP_CF_CONNECTING_IP="102.164.5.6", HTTP_DO_CONNECTING_IP="196.207.3.4"))
        == "102.164.5.6"
    )
    # En-tête falsifié non-IP : ignoré.
    assert client_ip(_req(REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="<script>")) == "10.0.0.1"


def _payload(i: int) -> dict:
    return {
        "email": f"proxy{i}@example.com",
        "username": f"proxyuser{i}",
        "password": "Bonjour-Dakar-2026",
        "password_confirm": "Bonjour-Dakar-2026",
        "date_of_birth": "1995-05-17",
        "terms_accepted": True,
    }


def test_users_behind_same_proxy_are_not_throttled_together(api_client, settings):
    """Avant le correctif : tous les visiteurs partageaient l'IP du load balancer."""
    settings.RATELIMIT_ENABLE = True
    for i in range(12):
        resp = api_client.post(
            reverse("auth-register"),
            _payload(i),
            format="json",
            REMOTE_ADDR="10.0.0.1",
            HTTP_X_FORWARDED_FOR=f"41.82.0.{i + 1}",
        )
        assert resp.status_code == 201, (i, resp.content)


def test_rate_limit_returns_429_with_readable_message(api_client, settings):
    settings.RATELIMIT_ENABLE = True
    last = None
    for _ in range(25):
        last = api_client.post(
            reverse("auth-login"),
            {"email": "ghost@example.com", "password": "nope-nope-nope"},
            format="json",
            HTTP_X_FORWARDED_FOR="41.82.9.9",
        )
    assert last.status_code == 429
    assert "Trop de tentatives" in last.json()["detail"]


def test_register_logs_user_in(api_client):
    from django.conf import settings as dj

    resp = api_client.post(reverse("auth-register"), _payload(99), format="json")
    assert resp.status_code == 201
    body = resp.json()
    assert body["access"]
    assert body["user"]["username"] == "proxyuser99"
    assert dj.REFRESH_COOKIE_NAME in resp.cookies


def test_resilient_cache_survives_redis_outage():
    from config.cache import ResilientRedisCache

    cache = ResilientRedisCache("redis://127.0.0.1:6399/0", {})
    assert cache.add("k", 1, 10) is False
    assert cache.get("k", "default") == "default"
    with pytest.raises(ValueError):
        cache.incr("k")
