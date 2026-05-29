"""Suivi des acquis des tutoriels (écrite à la main)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_twofactor"),
    ]

    operations = [
        migrations.CreateModel(
            name="GuideProgress",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("key", models.CharField(max_length=120)),
                ("completed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="guide_progress",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="guideprogress",
            index=models.Index(fields=["user"], name="accounts_gu_user_id_idx"),
        ),
        migrations.AddConstraint(
            model_name="guideprogress",
            constraint=models.UniqueConstraint(fields=["user", "key"], name="uniq_guide_progress"),
        ),
    ]
