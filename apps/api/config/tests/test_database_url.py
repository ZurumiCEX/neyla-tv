"""DATABASE_URL (Neon, Fly…) prioritaire sur les variables POSTGRES_*."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[2]


def _databases(**env) -> dict:
    code = (
        "import json, django; from django.conf import settings; django.setup();"
        "print(json.dumps(settings.DATABASES['default'], default=str))"
    )
    full_env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
    full_env.update(DJANGO_SETTINGS_MODULE="config.settings.dev", **env)
    out = subprocess.run(
        [sys.executable, "-c", code],
        cwd=API_DIR,
        env=full_env,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_database_url_overrides_postgres_vars():
    db = _databases(
        DATABASE_URL="postgres://neon_user:secret@ep-demo.eu-central-1.aws.neon.tech/neyla",
        POSTGRES_HOST="localhost",
    )
    assert db["HOST"] == "ep-demo.eu-central-1.aws.neon.tech"
    assert db["NAME"] == "neyla"
    assert db["USER"] == "neon_user"
    assert db["OPTIONS"]["sslmode"] == "require"
    assert db["CONN_HEALTH_CHECKS"] is True


def test_postgres_vars_used_without_database_url():
    db = _databases(POSTGRES_HOST="db.local", POSTGRES_DB="neyla_test")
    assert db["HOST"] == "db.local"
    assert db["NAME"] == "neyla_test"
