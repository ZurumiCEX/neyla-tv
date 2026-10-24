"""Sécurité des comptes : anti-rejeu TOTP, codes de secours, passkeys, mots de passe,
verrouillage par compte, 2FA staff, retraits, origine WebSocket."""

from __future__ import annotations

import time
from unittest import mock

import pytest
from django.core import mail
from django.urls import reverse
from rest_framework.test import APIClient

from accounts import passkeys, totp, two_factor
from accounts.factories import UserFactory
from accounts.models import Passkey, TwoFactor, User
from accounts.tokens import make_reset_token

pytestmark = pytest.mark.django_db

PASSWORD = "correct-horse-battery-staple"


def _code(secret: str, offset: int = 0) -> str:
    return totp._hotp(secret, int(time.time() // totp.PERIOD) + offset)


def _login(user) -> APIClient:
    client = APIClient()
    resp = client.post(
        reverse("auth-login"), {"email": user.email, "password": PASSWORD}, format="json"
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['access']}")
    return client


def _enable(user) -> tuple[str, list[str]]:
    _, secret = two_factor.begin_setup(user)
    codes = two_factor.enable(user, _code(secret, -1))
    return secret, codes


def test_secret_is_encrypted_at_rest_and_totp_cannot_be_replayed():
    user = UserFactory()
    secret, _ = _enable(user)
    stored = TwoFactor.objects.get(user=user).secret
    assert stored.startswith("enc:") and secret not in stored
    code = _code(secret)
    assert two_factor.verify(user, code) is True
    assert two_factor.verify(user, code) is False  # rejeu refusé
    assert two_factor.verify(user, _code(secret, -1)) is False  # période antérieure


def test_recovery_code_works_once_and_can_be_regenerated():
    user = UserFactory()
    _, codes = _enable(user)
    assert two_factor.verify(user, codes[0]) is True
    assert two_factor.verify(user, codes[0]) is False
    assert two_factor.remaining_recovery_codes(User.objects.get(pk=user.pk)) == 9
    new_codes = two_factor.regenerate_recovery_codes(user)
    assert len(new_codes) == 10
    assert two_factor.verify(user, codes[1]) is False  # anciens codes invalidés
    assert two_factor.verify(user, new_codes[0]) is True


def test_disable_2fa_requires_password():
    user = UserFactory()
    client = _login(user)
    _, secret = two_factor.begin_setup(user)
    two_factor.enable(user, _code(secret, -1))
    resp = client.post(reverse("auth-2fa-disable"), {"code": _code(secret)}, format="json")
    assert resp.status_code == 403
    assert TwoFactor.objects.filter(user=user, enabled=True).exists()


def test_account_lockout_after_failed_logins():
    user = UserFactory()
    client = APIClient()
    for _ in range(5):
        client.post(reverse("auth-login"), {"email": user.email, "password": "bad"}, format="json")
    resp = client.post(
        reverse("auth-login"), {"email": user.email, "password": PASSWORD}, format="json"
    )
    assert resp.status_code == 429


def test_password_change_revokes_other_sessions_and_emails():
    user = UserFactory()
    other_device = _login(user)
    client = _login(user)
    resp = client.post(
        reverse("auth-password-change"),
        {"password": PASSWORD, "new_password": "Une-Nouvelle-Phrase-42"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["sessions_revoked"] >= 1
    user.refresh_from_db()
    assert user.check_password("Une-Nouvelle-Phrase-42")
    assert any("mot de passe" in m.subject.lower() for m in mail.outbox)
    assert other_device is not None
    wrong = client.post(
        reverse("auth-password-change"),
        {"password": "faux", "new_password": "Encore-Une-Autre-43"},
        format="json",
    )
    assert wrong.status_code == 403


def test_reset_token_is_single_use():
    user = UserFactory()
    token = make_reset_token(user)
    client = APIClient()
    url = reverse("auth-password-reset-confirm")
    assert (
        client.post(
            url, {"token": token, "password": "Phrase-Secrete-77"}, format="json"
        ).status_code
        == 200
    )
    again = client.post(url, {"token": token, "password": "Phrase-Secrete-78"}, format="json")
    assert again.status_code == 400


def test_passkey_register_and_login_flow():
    user = UserFactory()
    client = _login(user)
    assert (
        client.post(
            reverse("auth-passkey-register-options"), {"password": "faux"}, format="json"
        ).status_code
        == 403
    )
    options = client.post(
        reverse("auth-passkey-register-options"), {"password": PASSWORD}, format="json"
    ).json()
    assert options["rp"]["id"] == "localhost"
    assert options["authenticatorSelection"]["residentKey"] == "required"

    fake_reg = mock.Mock(credential_id=b"cred-1", credential_public_key=b"pk", sign_count=0)
    with mock.patch.object(passkeys, "verify_registration_response", return_value=fake_reg):
        resp = client.post(
            reverse("auth-passkey-register-verify"),
            {
                "credential": {"id": "Y3JlZC0x", "response": {"transports": ["internal"]}},
                "name": "Mon téléphone",
            },
            format="json",
        )
    assert resp.status_code == 201
    key = Passkey.objects.get(user=user)
    assert key.name == "Mon téléphone" and key.transports == ["internal"]

    anon = APIClient()
    start = anon.post(reverse("auth-passkey-login-options")).json()
    assert start["handle"] and start["options"]["challenge"]
    with mock.patch.object(
        passkeys, "verify_authentication_response", return_value=mock.Mock(new_sign_count=3)
    ):
        login = anon.post(
            reverse("auth-passkey-login-verify"),
            {"handle": start["handle"], "credential": {"id": key.credential_id}},
            format="json",
        )
    assert login.status_code == 200 and "access" in login.json()
    key.refresh_from_db()
    assert key.sign_count == 3
    # Un défi ne sert qu'une fois.
    replay = anon.post(
        reverse("auth-passkey-login-verify"),
        {"handle": start["handle"], "credential": {"id": key.credential_id}},
        format="json",
    )
    assert replay.status_code == 401


def test_staff_console_requires_strong_auth_when_enabled(settings):
    settings.REQUIRE_STAFF_2FA = True
    admin = UserFactory(role=User.Role.ADMIN)
    client = _login(admin)
    resp = client.get("/api/admin/users")
    assert resp.status_code == 403
    assert resp.json()["code"] == "two_factor_required"
    Passkey.objects.create(user=admin, credential_id="x", public_key="y")
    assert client.get("/api/admin/users").status_code == 200


def test_ws_origin_validation(settings):
    from config.ws_origin import origin_allowed

    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ["neyla-api.fly.dev"]
    settings.CORS_ALLOWED_ORIGINS = ["https://neyla.vercel.app"]
    settings.CORS_ALLOWED_ORIGIN_REGEXES = [r"^https://neyla-tv-.*\.vercel\.app$"]
    assert origin_allowed("https://neyla.vercel.app")
    assert origin_allowed("https://neyla-tv-git-main.vercel.app")
    assert origin_allowed("https://neyla-api.fly.dev")
    assert not origin_allowed("https://evil.example")
    assert origin_allowed("")  # client non navigateur


def test_trusted_client_ip_header_ignores_spoofed_forwarded_for(settings):
    from django.test import RequestFactory

    from config.client_ip import client_ip

    settings.CLIENT_IP_HEADER = "Fly-Client-IP"
    req = RequestFactory().get(
        "/",
        HTTP_X_FORWARDED_FOR="1.2.3.4",
        HTTP_FLY_CLIENT_IP="41.82.10.20",
        REMOTE_ADDR="10.0.0.1",
    )
    assert client_ip(req) == "41.82.10.20"
    spoof = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="1.2.3.4", REMOTE_ADDR="10.0.0.1")
    assert client_ip(spoof) == "10.0.0.1"
