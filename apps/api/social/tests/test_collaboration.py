"""Tests collaborations entre créateurs."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from channels_app.models import Channel
from social.models import Collaboration

pytestmark = pytest.mark.django_db


def test_collaborations_requires_auth(api_client):
    assert api_client.get(reverse("collaborations")).status_code == 401


def test_invite_creates_pending(auth_client_factory):
    a, b = UserFactory(), UserFactory(username="partner")
    resp = auth_client_factory(a).post(
        reverse("collaborations"), {"username": "partner"}, format="json"
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"
    assert Collaboration.objects.filter(inviter=a, invitee=b).exists()


def test_cannot_invite_self(auth_client_factory):
    a = UserFactory(username="solo")
    resp = auth_client_factory(a).post(
        reverse("collaborations"), {"username": "solo"}, format="json"
    )
    assert resp.status_code == 400


def test_invite_blocked_when_closed(auth_client_factory):
    a, b = UserFactory(), UserFactory(username="closed")
    Channel.objects.filter(user=b).update(collaborations_open=False)
    resp = auth_client_factory(a).post(
        reverse("collaborations"), {"username": "closed"}, format="json"
    )
    assert resp.status_code == 400


def test_accept_then_listed_active(auth_client_factory):
    a, b = UserFactory(), UserFactory(username="mate")
    collab = Collaboration.objects.create(inviter=a, invitee=b)
    resp = auth_client_factory(b).post(
        reverse("collaboration-detail", kwargs={"pk": collab.id}),
        {"action": "accept"},
        format="json",
    )
    assert resp.status_code == 200
    data = auth_client_factory(a).get(reverse("collaborations")).json()
    assert [c["user"]["username"] for c in data["active"]] == ["mate"]


def test_incoming_and_outgoing_split(auth_client_factory):
    a, b = UserFactory(username="aaa"), UserFactory(username="bbb")
    Collaboration.objects.create(inviter=a, invitee=b)
    out = auth_client_factory(a).get(reverse("collaborations")).json()
    inc = auth_client_factory(b).get(reverse("collaborations")).json()
    assert len(out["outgoing"]) == 1 and len(out["incoming"]) == 0
    assert len(inc["incoming"]) == 1 and len(inc["outgoing"]) == 0


def test_remove_collaboration(auth_client_factory):
    a, b = UserFactory(), UserFactory()
    collab = Collaboration.objects.create(
        inviter=a, invitee=b, status=Collaboration.Status.ACCEPTED
    )
    resp = auth_client_factory(b).delete(reverse("collaboration-detail", kwargs={"pk": collab.id}))
    assert resp.status_code == 204
    assert not Collaboration.objects.filter(id=collab.id).exists()
