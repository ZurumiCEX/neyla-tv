from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_follow_requires_auth(api_client):
    response = api_client.post(reverse("follows-target", kwargs={"username": "x"}))
    assert response.status_code == 401


def test_follow_then_unfollow(auth_client_factory):
    me = UserFactory(username="me1")
    UserFactory(username="streamer1")
    client = auth_client_factory(me)

    create = client.post(reverse("follows-target", kwargs={"username": "streamer1"}))
    assert create.status_code == 201
    assert create.json()["following"] is True

    delete = client.delete(reverse("follows-target", kwargs={"username": "streamer1"}))
    assert delete.status_code == 204


def test_follow_status_endpoint(auth_client_factory):
    me = UserFactory(username="me2")
    UserFactory(username="streamer2")
    client = auth_client_factory(me)

    before = client.get(reverse("follows-status", kwargs={"username": "streamer2"}))
    assert before.json() == {"following": False}

    client.post(reverse("follows-target", kwargs={"username": "streamer2"}))
    after = client.get(reverse("follows-status", kwargs={"username": "streamer2"}))
    assert after.json() == {"following": True}


def test_my_followings_lists_followed_channels(auth_client_factory):
    me = UserFactory(username="me3")
    UserFactory(username="streamerA")
    UserFactory(username="streamerB")
    client = auth_client_factory(me)
    client.post(reverse("follows-target", kwargs={"username": "streamerA"}))
    client.post(reverse("follows-target", kwargs={"username": "streamerB"}))

    response = client.get(reverse("follows-me"))
    assert response.status_code == 200
    results = response.json()["results"]
    slugs = [c["slug"] for c in results]
    assert set(slugs) == {"streamera", "streamerb"}
    assert all("viewers" in c for c in results)


def test_self_follow_rejected(auth_client_factory):
    me = UserFactory(username="selfme")
    client = auth_client_factory(me)
    response = client.post(reverse("follows-target", kwargs={"username": "selfme"}))
    assert response.status_code == 400
