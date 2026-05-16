"""Factories pour les tests."""

from __future__ import annotations

import factory

from .models import User


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    username = factory.Sequence(lambda n: f"user{n}")
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **_kwargs):
        password = extracted or "correct-horse-battery-staple"
        self.set_password(password)
        if create:
            self.save(update_fields=["password"])
