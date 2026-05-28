"""Tests admin : liste des utilisateurs + changement de rôle (gating par rôle)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User

pytestmark = pytest.mark.django_db


def test_admin_users_forbidden_for_non_admin(auth_client_factory):
    assert auth_client_factory(UserFactory()).get(reverse("admin-users")).status_code == 403


def test_admin_users_list_and_filter(auth_client_factory):
    admin = UserFactory(role=User.Role.ADMIN)
    UserFactory(username="alice")
    client = auth_client_factory(admin)
    resp = client.get(reverse("admin-users"), {"q": "alice"})
    assert resp.status_code == 200
    usernames = [u["username"] for u in resp.json()["results"]]
    assert "alice" in usernames


def test_admin_can_change_role(auth_client_factory):
    admin = UserFactory(role=User.Role.ADMIN)
    target = UserFactory()
    resp = auth_client_factory(admin).patch(
        reverse("admin-user-detail", kwargs={"pk": target.pk}),
        {"role": User.Role.MODERATOR},
        format="json",
    )
    assert resp.status_code == 200
    target.refresh_from_db()
    assert target.role == User.Role.MODERATOR
