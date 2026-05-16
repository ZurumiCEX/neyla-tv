"""Tests des tokens signés (email-verify et password-reset)."""

from __future__ import annotations

import pytest
from django.core.signing import TimestampSigner

from accounts.tokens import (
    EMAIL_VERIFY_PURPOSE,
    EMAIL_VERIFY_TTL,
    PASSWORD_RESET_PURPOSE,
    InvalidToken,
    make_token,
    read_token,
)


def test_round_trip_email_verify():
    token = make_token(42, EMAIL_VERIFY_PURPOSE)
    assert read_token(token, EMAIL_VERIFY_PURPOSE, EMAIL_VERIFY_TTL) == 42


def test_wrong_purpose_is_rejected():
    token = make_token(42, EMAIL_VERIFY_PURPOSE)
    with pytest.raises(InvalidToken):
        read_token(token, PASSWORD_RESET_PURPOSE, EMAIL_VERIFY_TTL)


def test_tampered_token_is_rejected():
    token = make_token(42, EMAIL_VERIFY_PURPOSE) + "x"
    with pytest.raises(InvalidToken):
        read_token(token, EMAIL_VERIFY_PURPOSE, EMAIL_VERIFY_TTL)


def test_garbage_payload_is_rejected():
    # Signer correctement un payload non-numérique pour exercer le ValueError.
    bad = TimestampSigner(salt=EMAIL_VERIFY_PURPOSE).sign("not-an-int")
    with pytest.raises(InvalidToken):
        read_token(bad, EMAIL_VERIFY_PURPOSE, EMAIL_VERIFY_TTL)


def test_expired_token_is_rejected():
    token = make_token(42, EMAIL_VERIFY_PURPOSE)
    with pytest.raises(InvalidToken):
        read_token(token, EMAIL_VERIFY_PURPOSE, max_age=0)
