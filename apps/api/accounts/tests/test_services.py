"""Tests des services métier (register, verify, reset)."""

from __future__ import annotations

import pytest
from django.contrib.auth.password_validation import ValidationError

from accounts.factories import UserFactory
from accounts.services import (
    RegistrationError,
    register_user,
    reset_password_with_token,
    verify_email_token,
)
from accounts.tokens import (
    EMAIL_VERIFY_PURPOSE,
    PASSWORD_RESET_PURPOSE,
    InvalidToken,
    make_token,
)

pytestmark = pytest.mark.django_db


def test_register_user_ok():
    user = register_user(
        email="alice@example.com",
        username="alice",
        password="correct-horse-battery-staple",
    )
    assert user.pk is not None
    assert user.username == "alice"
    assert user.check_password("correct-horse-battery-staple")


def test_register_user_lowercases_username():
    user = register_user(
        email="bob@example.com",
        username="BoB",
        password="correct-horse-battery-staple",
    )
    assert user.username == "bob"


def test_register_user_duplicate_email_rejected():
    UserFactory(email="dup@example.com", username="dup")
    with pytest.raises(RegistrationError):
        register_user(
            email="dup@example.com",
            username="other",
            password="correct-horse-battery-staple",
        )


def test_register_user_reserved_username_rejected():
    with pytest.raises(RegistrationError):
        register_user(
            email="admin@example.com",
            username="admin",
            password="correct-horse-battery-staple",
        )


def test_register_user_weak_password_rejected():
    with pytest.raises(ValidationError):
        register_user(email="weak@example.com", username="weak", password="short")


def test_verify_email_marks_user_verified():
    user = UserFactory(email_verified_at=None)
    token = make_token(user.pk, EMAIL_VERIFY_PURPOSE)
    verified = verify_email_token(token)
    assert verified.is_email_verified


def test_verify_email_is_idempotent():
    user = UserFactory(email_verified_at=None)
    token = make_token(user.pk, EMAIL_VERIFY_PURPOSE)
    first = verify_email_token(token).email_verified_at
    again = verify_email_token(token).email_verified_at
    assert first == again


def test_verify_email_with_bad_token_rejected():
    with pytest.raises(InvalidToken):
        verify_email_token("nope")


def test_reset_password_changes_hash():
    user = UserFactory(password="old-password-12345")
    token = make_token(user.pk, PASSWORD_RESET_PURPOSE)
    reset_password_with_token(token, "new-password-67890")
    user.refresh_from_db()
    assert user.check_password("new-password-67890")
    assert not user.check_password("old-password-12345")


def test_reset_password_rejects_weak():
    user = UserFactory()
    token = make_token(user.pk, PASSWORD_RESET_PURPOSE)
    with pytest.raises(ValidationError):
        reset_password_with_token(token, "short")
