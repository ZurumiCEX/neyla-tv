"""Tests v2.5 modération : import mots interdits, file de signalements, ban depuis report."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from accounts.models import User
from channels_app.models import Channel
from chat.models import ChatBan
from moderation import services
from moderation.models import BannedWord, Report

pytestmark = pytest.mark.django_db


def test_import_banned_words_dedupes():
    result = services.import_banned_words("spam, INSULTE\nspam;arnaque")
    assert result["added"] == 3
    assert BannedWord.objects.filter(word="insulte").exists()
    again = services.import_banned_words("spam")
    assert again["added"] == 0


def test_import_endpoint_requires_moderator(auth_client_factory):
    resp = auth_client_factory(UserFactory()).post(
        reverse("moderation-banned-words-import"), {"words": "x"}, format="json"
    )
    assert resp.status_code == 403


def test_import_endpoint_ok_for_moderator(auth_client_factory):
    mod = UserFactory(role=User.Role.MODERATOR)
    resp = auth_client_factory(mod).post(
        reverse("moderation-banned-words-import"), {"words": "a,b,c"}, format="json"
    )
    assert resp.status_code == 201
    assert resp.json()["added"] == 3


def test_reports_list_and_patch(auth_client_factory):
    reporter = UserFactory()
    report = services.create_report(reporter, reason=Report.Reason.SPAM, details="x")
    mod = UserFactory(role=User.Role.MODERATOR)
    client = auth_client_factory(mod)
    listed = client.get(reverse("moderation-reports"))
    assert listed.status_code == 200
    assert listed.json()["count"] == 1
    patched = client.patch(
        reverse("moderation-report-detail", kwargs={"pk": report.id}),
        {"status": "dismissed", "resolution": "Rien à signaler", "assign_to_self": True},
        format="json",
    )
    assert patched.status_code == 200
    report.refresh_from_db()
    assert report.status == Report.Status.DISMISSED
    assert report.resolved_at is not None
    assert report.assigned_to_id == mod.id


def test_ban_from_report_creates_chatban(auth_client_factory):
    reporter = UserFactory()
    target = UserFactory()
    channel = Channel.objects.get(user=UserFactory())
    report = services.create_report(
        reporter,
        reason=Report.Reason.HARASSMENT,
        target_username=target.username,
        channel_slug=channel.slug,
    )
    mod = UserFactory(role=User.Role.MODERATOR)
    resp = auth_client_factory(mod).patch(
        reverse("moderation-report-detail", kwargs={"pk": report.id}),
        {"ban": True},
        format="json",
    )
    assert resp.status_code == 200
    assert ChatBan.objects.filter(channel=channel, user=target).exists()
    report.refresh_from_db()
    assert report.status == Report.Status.ACTIONED
