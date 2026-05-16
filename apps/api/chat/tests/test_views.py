"""Tests de l'endpoint historique."""

from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.factories import UserFactory
from channels_app.models import Channel
from chat.redis_store import append_message

pytestmark = pytest.mark.django_db


def test_history_returns_empty_for_unknown(api_client_phase4=None):
    client = APIClient()
    response = client.get(reverse("chat-history", kwargs={"slug": "ghost"}))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_history_returns_appended_messages():
    # On crée le user/channel via une fixture sync wrappée.
    from channels.db import database_sync_to_async

    user = await database_sync_to_async(UserFactory)(username="histu")
    channel = await database_sync_to_async(Channel.objects.get)(user=user)

    await append_message(
        channel.id,
        {"id": "1", "user": {"username": "x", "display_name": "X"}, "content": "hi", "ts": 1},
    )

    client = APIClient()
    response = await database_sync_to_async(client.get)(
        reverse("chat-history", kwargs={"slug": "histu"})
    )
    assert response.status_code == 200
    messages = response.json()["messages"]
    assert any(m["content"] == "hi" for m in messages)
