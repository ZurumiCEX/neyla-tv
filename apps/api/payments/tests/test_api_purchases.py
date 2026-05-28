"""Tests endpoint historique des achats fiat."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from payments import services

pytestmark = pytest.mark.django_db


def test_purchases_requires_auth(api_client):
    assert api_client.get(reverse("payments-purchases")).status_code == 401


def test_purchases_lists_only_own(auth_client_factory):
    user = UserFactory()
    other = UserFactory()
    services.create_purchase(user, 100)
    services.create_purchase(other, 500)
    client = auth_client_factory(user)
    response = client.get(reverse("payments-purchases"))
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["credits"] == 100
    assert "status" in results[0]
