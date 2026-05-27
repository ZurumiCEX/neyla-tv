"""Tests rôle utilisateur + permissions basées sur le rôle."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User
from accounts.permissions import IsAdminRole, IsModerator, IsSupport

pytestmark = pytest.mark.django_db


def test_default_role_is_user():
    assert UserFactory().role == User.Role.USER


def test_me_exposes_role(auth_client_factory):
    user = UserFactory(role=User.Role.MODERATOR)
    data = auth_client_factory(user).get(reverse("auth-me")).json()
    assert data["role"] == "moderator"


class _Req:
    def __init__(self, user):
        self.user = user


@pytest.mark.parametrize(
    "role,perm,expected",
    [
        (User.Role.ADMIN, IsAdminRole, True),
        (User.Role.MODERATOR, IsAdminRole, False),
        (User.Role.MODERATOR, IsModerator, True),
        (User.Role.SUPPORT, IsModerator, False),
        (User.Role.SUPPORT, IsSupport, True),
        (User.Role.USER, IsSupport, False),
    ],
)
def test_role_permissions(role, perm, expected):
    user = UserFactory(role=role)
    assert perm().has_permission(_Req(user), None) is expected
