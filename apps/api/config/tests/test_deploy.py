"""Déploiement : preflight, health check sans hôte connu, domaine Fly, URL Neon."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, override_settings

API_DIR = Path(__file__).resolve().parents[2]


@pytest.mark.django_db
def test_preflight_ok(capsys, settings):
    settings.SECRET_KEY = "x" * 50
    settings.REDIS_URL = "redis://cache.internal:6379/0"
    call_command("preflight")
    out = capsys.readouterr().out
    assert "configuration OK" in out
    assert "x" * 50 not in out


@pytest.mark.django_db
def test_preflight_fails_without_secret_key(capsys, settings):
    settings.SECRET_KEY = "dev-insecure-key"
    with pytest.raises(CommandError):
        call_command("preflight")
    assert "DJANGO_SECRET_KEY" in capsys.readouterr().err


@override_settings(ALLOWED_HOSTS=["neyla-tv.fly.dev"], DEBUG=False)
def test_livez_answers_whatever_the_host():
    client = Client(HTTP_HOST="172.19.0.10:8000")
    assert client.get("/api/livez").status_code == 200
    assert client.get("/api/healthz").status_code == 400  # les autres routes restent protégées


def _prod_settings(**env) -> dict:
    code = (
        "import json, django; from django.conf import settings; django.setup();"
        "print(json.dumps({'hosts': settings.ALLOWED_HOSTS, 'csrf': settings.CSRF_TRUSTED_ORIGINS,"
        " 'db': settings.DATABASES['default']}, default=str))"
    )
    full = {k: v for k, v in os.environ.items() if k not in ("DATABASE_URL", "FLY_APP_NAME")}
    full.update(DJANGO_SETTINGS_MODULE="config.settings.prod", DJANGO_SECRET_KEY="k" * 50, **env)
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=API_DIR, env=full, capture_output=True, text=True
    )
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_fly_app_name_is_allowed_automatically():
    data = _prod_settings(FLY_APP_NAME="neyla-tv")
    assert "neyla-tv.fly.dev" in data["hosts"]
    assert "https://neyla-tv.fly.dev" in data["csrf"]


def test_neon_url_with_channel_binding():
    data = _prod_settings(
        DATABASE_URL="postgresql://u:p@ep-x.eu-central-1.aws.neon.tech/neondb"
        "?sslmode=require&channel_binding=require"
    )
    assert data["db"]["HOST"] == "ep-x.eu-central-1.aws.neon.tech"
    assert data["db"]["OPTIONS"]["sslmode"] == "require"
    assert data["db"]["OPTIONS"]["channel_binding"] == "require"


def test_prod_without_secret_key_prints_clear_message():
    code = "import django; django.setup()"
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SECRET_KEY"}
    env["DJANGO_SETTINGS_MODULE"] = "config.settings.prod"
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=API_DIR, env=env, capture_output=True, text=True
    )
    assert out.returncode != 0
    assert "DJANGO_SECRET_KEY n'est pas défini" in out.stderr
