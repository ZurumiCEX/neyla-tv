"""Tests des services candidature streamer."""

from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from channels_app.models import Channel
from streamers import services
from streamers.models import StreamerApplication

pytestmark = pytest.mark.django_db


def test_submit_creates_pending_without_provisioning():
    user = UserFactory()
    application = services.submit_application(user, "je veux streamer")
    assert application.status == StreamerApplication.Status.PENDING
    assert not Channel.objects.get(user=user).is_provisioned


def test_approve_provisions_channel():
    user = UserFactory()
    application = services.submit_application(user)
    admin = UserFactory(is_staff=True)
    services.approve_application(application, admin)
    application.refresh_from_db()
    assert application.status == StreamerApplication.Status.APPROVED
    assert application.decided_by == admin
    assert Channel.objects.get(user=user).is_provisioned


def test_approve_is_idempotent():
    user = UserFactory()
    application = services.submit_application(user)
    admin = UserFactory(is_staff=True)
    services.approve_application(application, admin)
    channel = Channel.objects.get(user=user)
    uid = channel.live_input_uid
    services.approve_application(application, admin)
    channel.refresh_from_db()
    assert channel.live_input_uid == uid


def test_daily_quota_blocks_excess_approvals(settings):
    settings.STREAMER_DAILY_APPROVAL_QUOTA = 1
    admin = UserFactory(is_staff=True)
    first = services.submit_application(UserFactory())
    second = services.submit_application(UserFactory())
    services.approve_application(first, admin)
    with pytest.raises(services.QuotaExceededError):
        services.approve_application(second, admin)


def test_reject_then_reapply_resets_to_pending():
    user = UserFactory()
    application = services.submit_application(user)
    admin = UserFactory(is_staff=True)
    services.reject_application(application, admin, reason="pas maintenant")
    application.refresh_from_db()
    assert application.status == StreamerApplication.Status.REJECTED
    reapplied = services.submit_application(user, "je réessaie")
    assert reapplied.status == StreamerApplication.Status.PENDING
    assert reapplied.rejection_reason == ""


def test_already_streamer_cannot_resubmit():
    user = UserFactory()
    application = services.submit_application(user)
    admin = UserFactory(is_staff=True)
    services.approve_application(application, admin)
    with pytest.raises(services.AlreadyStreamerError):
        services.submit_application(user)
