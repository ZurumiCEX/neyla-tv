"""Fixtures partagées des tests uploads."""

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


@pytest.fixture(autouse=True)
def _media_root(settings, tmp_path):
    """Uploads écrits dans un dossier temporaire (mode local, sans R2)."""
    settings.MEDIA_ROOT = str(tmp_path)
    from django.core.files.storage import default_storage

    default_storage.__dict__.pop("base_location", None)
    default_storage.__dict__.pop("location", None)
    yield
