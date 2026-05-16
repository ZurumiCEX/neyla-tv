from __future__ import annotations

import factory

from .models import Game


class GameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Game
        django_get_or_create = ("slug",)

    slug = factory.Sequence(lambda n: f"game-{n}")
    name = factory.Sequence(lambda n: f"Game {n}")
