"""Fixtures partagées pour les tests d'auth."""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from accounts.factories import UserFactory


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user():
    return UserFactory()


@pytest.fixture
def auth_client(api_client, user):
    from rest_framework_simplejwt.tokens import RefreshToken

    access = str(RefreshToken.for_user(user).access_token)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return api_client


@pytest.fixture
def auth_client_factory():
    from rest_framework_simplejwt.tokens import RefreshToken

    def _make(u) -> APIClient:
        client = APIClient()
        access = str(RefreshToken.for_user(u).access_token)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        return client

    return _make
