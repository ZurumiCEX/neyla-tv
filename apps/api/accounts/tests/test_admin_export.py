"""Tests admin : export CSV global + actions métier."""

from __future__ import annotations

import pytest
from django.contrib.admin.sites import site

from accounts.factories import UserFactory
from accounts.models import User

pytestmark = pytest.mark.django_db


def test_export_csv_action_registered_globally():
    assert "export_as_csv" in site._actions


def test_export_csv_returns_csv():
    from config.admin_actions import export_as_csv

    UserFactory(username="csvuser")
    ma = site._registry[User]
    resp = export_as_csv(ma, None, User.objects.all())
    assert resp["Content-Type"] == "text/csv"
    body = resp.content.decode()
    assert "username" in body.splitlines()[0]
    assert "csvuser" in body


def test_payout_admin_has_resolve_actions():
    from payments.models import Payout

    ma = site._registry[Payout]
    assert "mark_paid" in ma.actions and "mark_failed" in ma.actions


def test_report_admin_inline_status_editable():
    from moderation.models import Report

    ma = site._registry[Report]
    assert "status" in ma.list_editable
