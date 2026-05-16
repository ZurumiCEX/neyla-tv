"""Tests de l'endpoint historique."""

from __future__ import annotations

import pytest
from asgiref.sync import async_to_sync
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.factories import UserFactory
from channels_app.models import Channel
from chat.redis_store import append_message

pytestmark = pytest.mark.django_db


def test_history_returns_404_for_unknown():
    client = APIClient()
    response = client.get(reverse("chat-history", kwargs={"slug": "ghost"}))
    assert response.status_code == 404


def test_history_returns_appended_messages():
    user = UserFactory(username="histu")
    channel = Channel.objects.get(user=user)

    async_to_sync(append_message)(
        channel.id,
        {
            "id": "1",
            "user": {"username": "x", "display_name": "X"},
            "content": "hi",
            "ts": 1,
        },
    )

    client = APIClient()
    response = client.get(reverse("chat-history", kwargs={"slug": "histu"}))
    assert response.status_code == 200
    messages = response.json()["messages"]
    assert any(m["content"] == "hi" for m in messages)
