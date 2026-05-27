"""Test : /api/auth/me expose is_streamer (true après provisioning)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel
from channels_app.services import provision_channel

pytestmark = pytest.mark.django_db


def test_is_streamer_false_before_provisioning(auth_client_factory):
    user = UserFactory()
    data = auth_client_factory(user).get(reverse("auth-me")).json()
    assert data["is_streamer"] is False


def test_is_streamer_true_after_provisioning(auth_client_factory):
    user = UserFactory()
    provision_channel(Channel.objects.get(user=user))
    data = auth_client_factory(user).get(reverse("auth-me")).json()
    assert data["is_streamer"] is True
