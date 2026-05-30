"""Tests du scoring + transitions d'état (Creator Application System)."""

from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from streamers import services
from streamers.models import StreamerApplication
from streamers.scoring import compute_score

pytestmark = pytest.mark.django_db


def test_compute_score_rewards_strong_signals():
    app = StreamerApplication(
        has_streamed=True,
        community_size="10k_plus",
        motivation="x" * 250,
        why_select="y" * 200,
        frequency="daily",
        setup=["pc", "webcam", "microphone"],
        platforms={"twitch": "t", "youtube": "y"},
    )
    # 20 (streamed) + 25 (community) + 20 (texte≥400) + 15 (daily) + 10 (setup) + 10 (2 socials)
    assert compute_score(app) == 100


def test_compute_score_minimal_profile_low():
    app = StreamerApplication(has_streamed=False, motivation="court")
    assert compute_score(app) < 20


def test_submit_application_persists_fields_and_score():
    user = UserFactory()
    app = services.submit_application(
        user,
        "Je veux divertir et fédérer.",
        fields={
            "has_streamed": True,
            "community_size": "100_1k",
            "frequency": "3_5_week",
            "setup": ["pc", "microphone"],
            "platforms": {"twitch": "https://twitch.tv/x"},
            "content_categories": ["gaming"],
            "rules_accepted": True,
        },
    )
    assert app.status == StreamerApplication.Status.PENDING
    assert app.has_streamed is True
    assert app.community_size == "100_1k"
    assert app.score > 0


def test_status_transitions_under_review_and_interview():
    admin = UserFactory(role="admin")
    app = services.submit_application(UserFactory(), "motivé", fields={"rules_accepted": True})
    services.set_under_review(app, admin)
    app.refresh_from_db()
    assert app.status == StreamerApplication.Status.UNDER_REVIEW
    services.request_interview(app, admin)
    app.refresh_from_db()
    assert app.status == StreamerApplication.Status.INTERVIEW


def test_admin_can_mark_under_review_and_interview(client):
    from accounts.models import User

    boss = User.objects.create_superuser(
        username="boss-cas", email="boss-cas@example.com", password="pw-12345"
    )
    app = services.submit_application(UserFactory(), "x", fields={"rules_accepted": True})
    client.force_login(boss)
    url = "/admin/streamers/streamerapplication/"
    resp = client.post(
        url,
        {"action": "mark_under_review", "_selected_action": [app.pk]},
        follow=True,
    )
    assert resp.status_code == 200
    app.refresh_from_db()
    assert app.status == StreamerApplication.Status.UNDER_REVIEW
