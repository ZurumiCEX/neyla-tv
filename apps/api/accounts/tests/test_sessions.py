"""Tests sessions d'appareil : login crée, liste, révocation."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.factories import UserFactory
from accounts.models import UserSession

pytestmark = pytest.mark.django_db

PASSWORD = "correct-horse-battery-staple"


def _login(user) -> APIClient:
    client = APIClient()
    resp = client.post(
        reverse("auth-login"),
        {"email": user.email, "password": PASSWORD},
        format="json",
    )
    assert resp.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['access']}")
    return client


def test_login_creates_session_marked_current():
    user = UserFactory()
    client = _login(user)
    resp = client.get(reverse("auth-sessions"))
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 1
    assert results[0]["is_current"] is True


def test_revoke_other_sessions_keeps_current():
    user = UserFactory()
    client_a = _login(user)
    _login(user)  # second device
    assert UserSession.objects.filter(user=user, revoked=False).count() == 2

    resp = client_a.post(reverse("auth-sessions-revoke-others"))
    assert resp.status_code == 200
    assert resp.json()["revoked"] == 1
    remaining = list(UserSession.objects.filter(user=user, revoked=False))
    assert len(remaining) == 1


def test_revoke_specific_session():
    user = UserFactory()
    client = _login(user)
    _login(user)  # second device
    sessions = list(UserSession.objects.filter(user=user))
    list_resp = client.get(reverse("auth-sessions")).json()["results"]
    current_id = next(s["id"] for s in list_resp if s["is_current"])
    target = next(s for s in sessions if s.id != current_id)
    resp = client.delete(reverse("auth-session-revoke", kwargs={"pk": target.id}))
    assert resp.status_code == 204
    target.refresh_from_db()
    assert target.revoked is True


def test_revoked_session_cannot_refresh():
    user = UserFactory()
    client_a = _login(user)
    client_b = _login(user)
    client_a.post(reverse("auth-sessions-revoke-others"))
    # client_b's refresh token (cookie) doit être blacklisté → refresh refusé.
    resp = client_b.post(reverse("auth-refresh"))
    assert resp.status_code == 401
