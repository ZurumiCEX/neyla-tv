"""Factories pour les tests."""

from __future__ import annotations

import factory

from accounts.factories import UserFactory

from .models import StreamerApplication


class StreamerApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StreamerApplication

    user = factory.SubFactory(UserFactory)
    motivation = "Je veux streamer."
