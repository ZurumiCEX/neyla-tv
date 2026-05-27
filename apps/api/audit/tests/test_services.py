"""Tests du journal d'audit + intégrations (approbation streamer, payout)."""

from __future__ import annotations

import pytest

from accounts.factories import UserFactory
from audit import services
from audit.models import AuditEvent

pytestmark = pytest.mark.django_db


def test_record_with_target():
    actor = UserFactory()
    target = UserFactory()
    event = services.record(actor, "test.action", target=target, meta={"x": 1})
    assert event.action == "test.action"
    assert event.target_type == "User"
    assert event.target_id == str(target.pk)
    assert event.meta == {"x": 1}


def test_approve_application_is_audited():
    from streamers import services as streamer_services

    user = UserFactory()
    admin = UserFactory(is_staff=True)
    application = streamer_services.submit_application(user)
    streamer_services.approve_application(application, admin)
    assert AuditEvent.objects.filter(action="streamer.approve", actor=admin).exists()


def test_payout_is_audited():
    from payments import services as pay_services

    user = UserFactory()
    pay_services.create_purchase(user, 100)
    pay_services.request_payout(user, 50)
    assert AuditEvent.objects.filter(action="payout.request", actor=user).exists()
