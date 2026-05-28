from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from catalog.factories import GameFactory
from channels_app.models import Channel

pytestmark = pytest.mark.django_db


def test_discover_live_returns_only_live_channels(api_client):
    UserFactory(username="onair1")
    UserFactory(username="offline1")
    Channel.objects.filter(slug="onair1").update(is_live=True)
    response = api_client.get(reverse("discover-live"))
    assert response.status_code == 200
    slugs = [c["slug"] for c in response.json()["results"]]
    assert "onair1" in slugs
    assert "offline1" not in slugs


def test_discover_categories_orders_by_live_count(api_client):
    valorant = GameFactory(slug="vlr", name="Valorant")
    lol = GameFactory(slug="lol", name="League")
    GameFactory(slug="empty", name="Empty")

    u1 = UserFactory(username="cat1")
    u2 = UserFactory(username="cat2")
    u3 = UserFactory(username="cat3")
    Channel.objects.filter(user=u1).update(is_live=True, category=valorant)
    Channel.objects.filter(user=u2).update(is_live=True, category=valorant)
    Channel.objects.filter(user=u3).update(is_live=True, category=lol)

    response = api_client.get(reverse("discover-categories"))
    assert response.status_code == 200
    results = response.json()["results"]
    by_slug = {g["slug"]: g for g in results}
    assert by_slug["vlr"]["live_count"] == 2
    assert by_slug["lol"]["live_count"] == 1
    assert "viewers" in by_slug["vlr"]
    # "empty" doit avoir 0 et venir après.
    order = [g["slug"] for g in results]
    assert order.index("vlr") < order.index("lol")
    assert order.index("lol") < order.index("empty")


def test_discover_category_returns_live_in_that_game(api_client):
    valorant = GameFactory(slug="vlr2", name="Valorant 2")
    u = UserFactory(username="catstreamer")
    Channel.objects.filter(user=u).update(is_live=True, category=valorant)
    response = api_client.get(reverse("discover-category", kwargs={"slug": "vlr2"}))
    assert response.status_code == 200
    payload = response.json()
    assert payload["category"]["slug"] == "vlr2"
    assert [c["slug"] for c in payload["results"]] == ["catstreamer"]


def test_discover_category_404(api_client):
    response = api_client.get(reverse("discover-category", kwargs={"slug": "ghost"}))
    assert response.status_code == 404


def test_discover_search_finds_channel_and_game(api_client):
    GameFactory(slug="mc-search", name="Minecraft Search")
    UserFactory(username="searchable", display_name="Search Streamer")
    response = api_client.get(reverse("discover-search"), {"q": "search"})
    assert response.status_code == 200
    data = response.json()
    channel_slugs = [c["slug"] for c in data["channels"]]
    game_slugs = [g["slug"] for g in data["games"]]
    assert "searchable" in channel_slugs
    assert "mc-search" in game_slugs


def test_discover_search_short_query_returns_empty(api_client):
    response = api_client.get(reverse("discover-search"), {"q": "a"})
    assert response.status_code == 200
    data = response.json()
    assert data == {"channels": [], "games": []}


def test_discover_search_matches_tags(api_client):
    user = UserFactory(username="taggedstreamer")
    channel = Channel.objects.get(user=user)
    channel.tags = ["speedrun", "retro"]
    channel.save(update_fields=["tags"])
    response = api_client.get(reverse("discover-search"), {"q": "speedrun"})
    assert response.status_code == 200
    slugs = [c["slug"] for c in response.json()["channels"]]
    assert "taggedstreamer" in slugs
