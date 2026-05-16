"""Migration initiale du modèle Channel."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0002_user_profile_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Channel",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                ),
                ("slug", models.SlugField(db_index=True, max_length=30, unique=True)),
                ("title", models.CharField(blank=True, max_length=140)),
                ("thumbnail_url", models.URLField(blank=True)),
                ("live_input_uid", models.CharField(blank=True, db_index=True, max_length=64)),
                ("rtmps_url", models.CharField(blank=True, max_length=200)),
                ("rtmps_key", models.CharField(blank=True, max_length=200)),
                ("hls_playback_url", models.URLField(blank=True)),
                ("is_live", models.BooleanField(db_index=True, default=False)),
                ("last_live_started_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="channel",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
