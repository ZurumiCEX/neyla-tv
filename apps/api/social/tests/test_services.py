from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from social.models import Follow
from social.services import FollowError, follow_user, is_following, unfollow_user

pytestmark = pytest.mark.django_db


def test_follow_user_creates_relation():
    a = UserFactory(username="a1")
    b = UserFactory(username="b1")
    follow_user(a, "b1")
    assert Follow.objects.filter(follower=a, followee=b).exists()


def test_follow_user_is_idempotent():
    a = UserFactory(username="a2")
    UserFactory(username="b2")
    follow_user(a, "b2")
    follow_user(a, "b2")
    assert Follow.objects.filter(follower=a).count() == 1


def test_follow_self_rejected():
    a = UserFactory(username="self1")
    with pytest.raises(FollowError):
        follow_user(a, "self1")


def test_follow_unknown_user_rejected():
    a = UserFactory(username="x1")
    with pytest.raises(FollowError):
        follow_user(a, "ghost")


def test_unfollow_user():
    a = UserFactory(username="a3")
    UserFactory(username="b3")
    follow_user(a, "b3")
    deleted = unfollow_user(a, "b3")
    assert deleted == 1
    assert not is_following(a, "b3")


def test_is_following():
    a = UserFactory(username="a4")
    UserFactory(username="b4")
    assert not is_following(a, "b4")
    follow_user(a, "b4")
    assert is_following(a, "b4")
