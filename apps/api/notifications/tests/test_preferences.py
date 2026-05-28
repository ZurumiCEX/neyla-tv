"""Tests v2.5 notifications : préférences, marquage unitaire, messagerie support."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User
from notifications import services
from notifications.models import Notification

pytestmark = pytest.mark.django_db


def test_disabled_preference_skips_creation():
    user = UserFactory()
    services.set_preferences(user, {Notification.Type.NEW_FOLLOWER: False})
    result = services.create_notification(user, Notification.Type.NEW_FOLLOWER)
    assert result is None
    assert Notification.objects.filter(recipient=user).count() == 0


def test_enabled_by_default():
    user = UserFactory()
    assert services.create_notification(user, Notification.Type.NEW_FOLLOWER) is not None


def test_preferences_endpoint_roundtrip(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    put = client.put(
        reverse("notifications-preferences"),
        {Notification.Type.TIP_RECEIVED: False},
        format="json",
    )
    assert put.status_code == 200
    assert put.json()[Notification.Type.TIP_RECEIVED] is False
    got = client.get(reverse("notifications-preferences")).json()
    assert got[Notification.Type.TIP_RECEIVED] is False
    assert got[Notification.Type.NEW_FOLLOWER] is True


def test_mark_one_read(auth_client_factory):
    user = UserFactory()
    notif = services.create_notification(user, Notification.Type.NEW_FOLLOWER)
    resp = auth_client_factory(user).post(
        reverse("notifications-read-one", kwargs={"pk": notif.id})
    )
    assert resp.status_code == 200
    notif.refresh_from_db()
    assert notif.read_at is not None


def test_support_message_requires_support_role(auth_client_factory):
    target = UserFactory()
    resp = auth_client_factory(UserFactory()).post(
        reverse("admin-support-message"),
        {"username": target.username, "title": "Hi", "body": "Test"},
        format="json",
    )
    assert resp.status_code == 403


def test_support_message_creates_notification(auth_client_factory):
    target = UserFactory()
    support = UserFactory(role=User.Role.SUPPORT)
    resp = auth_client_factory(support).post(
        reverse("admin-support-message"),
        {"username": target.username, "title": "Bonjour", "body": "Bienvenue"},
        format="json",
    )
    assert resp.status_code == 201
    assert Notification.objects.filter(
        recipient=target, type=Notification.Type.SUPPORT_MESSAGE
    ).exists()
