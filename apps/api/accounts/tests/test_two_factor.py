"""Tests 2FA : TOTP stdlib + flux setup/enable/login/disable."""

from __future__ import annotations

import time

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts import totp
from accounts.factories import UserFactory
from accounts.models import TwoFactor

pytestmark = pytest.mark.django_db

PASSWORD = "correct-horse-battery-staple"


def _current_code(secret: str) -> str:
    return totp._hotp(secret, int(time.time() // totp.PERIOD))


def _auth(user) -> APIClient:
    client = APIClient()
    resp = client.post(
        reverse("auth-login"),
        {"email": user.email, "password": PASSWORD},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['access']}")
    return client


def test_totp_roundtrip():
    secret = totp.generate_secret()
    assert totp.verify(secret, _current_code(secret))
    assert not totp.verify(secret, "000000")


def test_setup_then_enable_returns_recovery_codes():
    user = UserFactory()
    client = _auth(user)
    setup = client.post(reverse("auth-2fa-setup")).json()
    assert "secret" in setup and setup["otpauth_uri"].startswith("otpauth://")

    enable = client.post(
        reverse("auth-2fa-enable"), {"code": _current_code(setup["secret"])}, format="json"
    )
    assert enable.status_code == 200
    assert len(enable.json()["recovery_codes"]) == 10
    assert client.get(reverse("auth-me")).json()["two_factor_enabled"] is True


def test_enable_rejects_bad_code():
    user = UserFactory()
    client = _auth(user)
    client.post(reverse("auth-2fa-setup"))
    resp = client.post(reverse("auth-2fa-enable"), {"code": "000000"}, format="json")
    assert resp.status_code == 400


def _enable_2fa(user) -> tuple[APIClient, str]:
    client = _auth(user)
    secret = client.post(reverse("auth-2fa-setup")).json()["secret"]
    client.post(reverse("auth-2fa-enable"), {"code": _current_code(secret)}, format="json")
    return client, secret


def test_login_with_2fa_requires_second_factor():
    user = UserFactory()
    _, secret = _enable_2fa(user)

    fresh = APIClient()
    step1 = fresh.post(
        reverse("auth-login"), {"email": user.email, "password": PASSWORD}, format="json"
    )
    body = step1.json()
    assert body.get("two_factor_required") is True
    assert "access" not in body

    step2 = fresh.post(
        reverse("auth-2fa-login"),
        {"token": body["token"], "code": _current_code(secret)},
        format="json",
    )
    assert step2.status_code == 200
    assert "access" in step2.json()


def test_2fa_login_rejects_bad_code():
    user = UserFactory()
    _enable_2fa(user)
    fresh = APIClient()  # nouvelle session sans 2FA validée
    body = fresh.post(
        reverse("auth-login"), {"email": user.email, "password": PASSWORD}, format="json"
    ).json()
    resp = fresh.post(
        reverse("auth-2fa-login"), {"token": body["token"], "code": "000000"}, format="json"
    )
    assert resp.status_code == 401


def test_recovery_code_consumed_on_use():
    user = UserFactory()
    client = _auth(user)
    secret = client.post(reverse("auth-2fa-setup")).json()["secret"]
    codes = client.post(
        reverse("auth-2fa-enable"), {"code": _current_code(secret)}, format="json"
    ).json()["recovery_codes"]

    fresh = APIClient()
    body = fresh.post(
        reverse("auth-login"), {"email": user.email, "password": PASSWORD}, format="json"
    ).json()
    ok = fresh.post(
        reverse("auth-2fa-login"), {"token": body["token"], "code": codes[0]}, format="json"
    )
    assert ok.status_code == 200
    tf = TwoFactor.objects.get(user=user)
    assert len(tf.recovery_codes) == 9  # un code consommé


def test_disable_with_valid_code():
    user = UserFactory()
    client, secret = _enable_2fa(user)
    resp = client.post(reverse("auth-2fa-disable"), {"code": _current_code(secret)}, format="json")
    assert resp.status_code == 200
    assert not TwoFactor.objects.filter(user=user).exists()
