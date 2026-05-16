"""Factories pour les tests."""

from __future__ import annotations

import factory

from accounts.factories import UserFactory

from .models import Channel


class ChannelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Channel
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)
    slug = factory.LazyAttribute(lambda obj: obj.user.username)
