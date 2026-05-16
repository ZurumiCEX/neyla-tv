"""Tests d'intégration des endpoints d'auth."""

from __future__ import annotations

import pytest
from django.conf import settings
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.tokens import (
    EMAIL_VERIFY_PURPOSE,
    PASSWORD_RESET_PURPOSE,
    make_token,
)

pytestmark = pytest.mark.django_db


def test_register_creates_user_and_triggers_email(api_client, mailoutbox):
    response = api_client.post(
        reverse("auth-register"),
        {"email": "neo@example.com", "username": "neo", "password": "correct-horse-battery-staple"},
        format="json",
    )
    assert response.status_code == 201, response.content
    assert response.data["email"] == "neo@example.com"
    assert response.data["username"] == "neo"
    # send_email_verification est appelé .delay() — eager doit produire 1 mail.
    assert len(mailoutbox) == 1
    assert "neo@example.com" in mailoutbox[0].to


def test_register_duplicate_email_rejected(api_client):
    UserFactory(email="dup@example.com", username="dup")
    response = api_client.post(
        reverse("auth-register"),
        {
            "email": "dup@example.com",
            "username": "other",
            "password": "correct-horse-battery-staple",
        },
        format="json",
    )
    assert response.status_code == 400


def test_register_invalid_username_rejected(api_client):
    response = api_client.post(
        reverse("auth-register"),
        {"email": "x@example.com", "username": "AB", "password": "correct-horse-battery-staple"},
        format="json",
    )
    assert response.status_code == 400


def test_login_returns_access_and_sets_cookie(api_client, user):
    response = api_client.post(
        reverse("auth-login"),
        {"email": user.email, "password": "correct-horse-battery-staple"},
        format="json",
    )
    assert response.status_code == 200
    assert "access" in response.data
    assert settings.REFRESH_COOKIE_NAME in response.cookies
    cookie = response.cookies[settings.REFRESH_COOKIE_NAME]
    assert cookie["httponly"]
    assert cookie["samesite"].lower() == "lax"


def test_login_wrong_password_returns_401(api_client, user):
    response = api_client.post(
        reverse("auth-login"),
        {"email": user.email, "password": "wrong"},
        format="json",
    )
    assert response.status_code == 401


def test_login_unknown_email_returns_401(api_client):
    response = api_client.post(
        reverse("auth-login"),
        {"email": "ghost@example.com", "password": "irrelevant-12345"},
        format="json",
    )
    assert response.status_code == 401


def test_refresh_rotates_token(api_client, user):
    login = api_client.post(
        reverse("auth-login"),
        {"email": user.email, "password": "correct-horse-battery-staple"},
        format="json",
    )
    first_cookie = login.cookies[settings.REFRESH_COOKIE_NAME].value
    api_client.cookies[settings.REFRESH_COOKIE_NAME] = first_cookie

    refresh_response = api_client.post(reverse("auth-refresh"))
    assert refresh_response.status_code == 200
    assert "access" in refresh_response.data
    new_cookie = refresh_response.cookies[settings.REFRESH_COOKIE_NAME].value
    assert new_cookie != first_cookie


def test_refresh_without_cookie_returns_401(api_client):
    response = api_client.post(reverse("auth-refresh"))
    assert response.status_code == 401


def test_me_requires_auth(api_client):
    response = api_client.get(reverse("auth-me"))
    assert response.status_code == 401


def test_me_returns_profile(auth_client, user):
    response = auth_client.get(reverse("auth-me"))
    assert response.status_code == 200
    assert response.data["email"] == user.email
    assert response.data["username"] == user.username


def test_me_patch_updates_profile(auth_client):
    response = auth_client.patch(
        reverse("auth-me"),
        {"display_name": "Neo Anderson", "bio": "Hello world"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["display_name"] == "Neo Anderson"
    assert response.data["bio"] == "Hello world"


def test_email_verify_with_valid_token(api_client, user):
    user.email_verified_at = None
    user.save()
    token = make_token(user.pk, EMAIL_VERIFY_PURPOSE)
    response = api_client.post(reverse("auth-email-verify"), {"token": token}, format="json")
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.is_email_verified


def test_password_reset_request_does_not_leak(api_client):
    response = api_client.post(
        reverse("auth-password-reset-request"),
        {"email": "ghost@example.com"},
        format="json",
    )
    assert response.status_code == 200


def test_password_reset_confirm_updates_password(api_client, user):
    token = make_token(user.pk, PASSWORD_RESET_PURPOSE)
    response = api_client.post(
        reverse("auth-password-reset-confirm"),
        {"token": token, "password": "brand-new-pass-456"},
        format="json",
    )
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password("brand-new-pass-456")


def test_logout_clears_cookie(api_client, user):
    login = api_client.post(
        reverse("auth-login"),
        {"email": user.email, "password": "correct-horse-battery-staple"},
        format="json",
    )
    api_client.cookies[settings.REFRESH_COOKIE_NAME] = login.cookies[
        settings.REFRESH_COOKIE_NAME
    ].value
    response = api_client.post(reverse("auth-logout"))
    assert response.status_code == 204
    assert response.cookies[settings.REFRESH_COOKIE_NAME].value == ""
