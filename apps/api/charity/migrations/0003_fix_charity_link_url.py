"""Corrige les `link_url` des PlatformEvent miroirs (charity-*) qui pointaient
vers `/charity/<slug>` (404) — désormais ils ciblent `/charity`."""

from __future__ import annotations

from django.db import migrations


def fix_links(apps, schema_editor):
    PlatformEvent = apps.get_model("charity", "PlatformEvent")
    PlatformEvent.objects.filter(slug__startswith="charity-").update(link_url="/charity")


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [("charity", "0002_platformevent")]
    operations = [migrations.RunPython(fix_links, noop)]
