"""CORS : front et API sur des origines distinctes (dev, Vercel + API)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.django_db


def test_preflight_allows_credentials_and_idempotency_header(client):
    resp = client.options(
        "/api/payments/tip",
        HTTP_ORIGIN="http://localhost:3000",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS="content-type,authorization,idempotency-key",
    )
    assert resp["Access-Control-Allow-Origin"] == "http://localhost:3000"
    assert resp["Access-Control-Allow-Credentials"] == "true"
    assert "idempotency-key" in resp["Access-Control-Allow-Headers"]
