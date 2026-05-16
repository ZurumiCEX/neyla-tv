from __future__ import annotations

import factory

from accounts.factories import UserFactory

from .models import Follow


class FollowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Follow

    follower = factory.SubFactory(UserFactory)
    followee = factory.SubFactory(UserFactory)
