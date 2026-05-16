"""Tests du healthcheck : on mocke Redis pour ne pas dépendre du broker en CI."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_healthz_ok(client):
    with patch("health.views._check_redis", return_value=True):
        response = client.get(reverse("healthz"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["db"] is True
    assert payload["redis"] is True


@pytest.mark.django_db
def test_healthz_degraded_when_redis_down(client):
    with patch("health.views._check_redis", return_value=False):
        response = client.get(reverse("healthz"))
    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["redis"] is False
