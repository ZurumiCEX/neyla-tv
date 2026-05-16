from __future__ import annotations

import factory

from accounts.factories import UserFactory
from channels_app.factories import ChannelFactory

from .models import ChatBan


class ChatBanFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ChatBan

    channel = factory.SubFactory(ChannelFactory)
    user = factory.SubFactory(UserFactory)
    until = None
    reason = "test"
