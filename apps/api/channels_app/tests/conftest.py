"""Fixtures partagées des tests channels_app."""

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
