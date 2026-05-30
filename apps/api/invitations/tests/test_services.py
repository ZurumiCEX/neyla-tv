"""Tests invitations : génération, redemption, épuisement, compteur, inscription."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.services import register_user
from invitations import services
from invitations.models import Invite

pytestmark = pytest.mark.django_db


def test_create_and_redeem_links_inviter():
    inviter = UserFactory()
    invite = services.create_invite(inviter)
    newbie = UserFactory(email_verified_at=None)
    services.redeem(invite.code, newbie)
    newbie.refresh_from_db()
    invite.refresh_from_db()
    assert newbie.invited_by_id == inviter.id
    assert invite.used_count == 1
    # Avant vérif email, le filleul n'est pas encore « validé ».
    assert services.successful_count(inviter) == 0


def test_redeem_rejects_self_use():
    inviter = UserFactory()
    invite = services.create_invite(inviter)
    with pytest.raises(services.InviteError):
        services.redeem(invite.code, inviter)


def test_redeem_rejects_exhausted_code():
    inviter = UserFactory()
    invite = services.create_invite(inviter, max_uses=1)
    services.redeem(invite.code, UserFactory())
    with pytest.raises(services.InviteError):
        services.redeem(invite.code, UserFactory())


def test_try_redeem_is_silent_on_bad_code():
    user = UserFactory()
    assert services.try_redeem("NOPE", user) is None
    user.refresh_from_db()
    assert user.invited_by_id is None


def test_registration_with_invite_links_inviter():
    inviter = UserFactory()
    invite = services.create_invite(inviter, max_uses=5)
    user = register_user(
        email="newbie@example.com",
        username="newbie",
        password="correct-horse-battery-staple",
        invite_code=invite.code,
        terms_accepted=True,
    )
    assert user.invited_by_id == inviter.id


def test_invites_endpoint_create_and_list(auth_client_factory):
    user = UserFactory()
    client = auth_client_factory(user)
    created = client.post(reverse("invites"), {"max_uses": 3}, format="json")
    assert created.status_code == 201
    code = created.json()["code"]
    assert Invite.objects.filter(code=code, inviter=user).exists()
    listed = client.get(reverse("invites")).json()
    assert listed["successful_invites"] == 0
    assert any(i["code"] == code for i in listed["results"])
