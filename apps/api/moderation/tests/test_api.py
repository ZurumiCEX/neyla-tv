"""Tests modération : mots interdits + signalements."""

from __future__ import annotations

import pytest
from django.urls import reverse

from accounts.factories import UserFactory
from moderation import services
from moderation.models import BannedWord, Report

pytestmark = pytest.mark.django_db


def test_banned_word_stored_lowercase():
    bw = BannedWord.objects.create(word="  BadWord ")
    assert bw.word == "badword"


def test_contains_banned_word():
    banned = {"badword"}
    assert services.contains_banned_word("ceci est un BadWord ici", banned)
    assert not services.contains_banned_word("texte propre", banned)


def test_report_requires_auth(api_client):
    assert api_client.post(reverse("reports-create")).status_code == 401


def test_create_report(auth_client_factory):
    streamer = UserFactory(username="target1")
    client = auth_client_factory(UserFactory())
    response = client.post(
        reverse("reports-create"),
        {"reason": "spam", "target_username": "target1", "details": "spam massif"},
        format="json",
    )
    assert response.status_code == 201
    report = Report.objects.get()
    assert report.target_user == streamer
    assert report.reason == "spam"
    assert report.status == Report.Status.OPEN


def test_create_report_invalid_reason(auth_client_factory):
    client = auth_client_factory(UserFactory())
    response = client.post(reverse("reports-create"), {"reason": "nope"}, format="json")
    assert response.status_code == 400
