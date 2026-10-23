"""Fixtures partagées des tests payments."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def auth_client_factory():
    def _make(user) -> APIClient:
        client = APIClient()
        access = str(RefreshToken.for_user(user).access_token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        return client

    return _make


@pytest.fixture
def earning_streamer(settings):
    """Streamer approuvé ayant GAGNÉ de l'Aura (tips) → solde retirable réel.

    Le seuil de retrait est abaissé pour garder des montants lisibles.
    """
    settings.WITHDRAWAL_MIN_AURA = 10

    def _make(tip_total: int = 1000):
        from accounts.factories import UserFactory
        from channels_app.testing import provisioned_channel
        from payments import services

        streamer = UserFactory()
        channel = provisioned_channel(streamer)
        fan = UserFactory()
        services.create_purchase(fan, tip_total)
        services.send_tip(fan, channel.slug, tip_total)
        return streamer

    return _make
