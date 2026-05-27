"""Factories pour les tests."""

from __future__ import annotations

import factory

from accounts.factories import UserFactory

from .models import Notification


class NotificationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory)
    type = Notification.Type.NEW_FOLLOWER
