"""Workflow de traitement des signalements (assigned_to, resolution) — à la main."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("moderation", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="assigned_to",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reports_assigned",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="report",
            name="resolution",
            field=models.TextField(blank=True, max_length=1000),
        ),
        migrations.AddField(
            model_name="report",
            name="resolved_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
