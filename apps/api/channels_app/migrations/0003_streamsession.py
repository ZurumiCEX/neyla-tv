"""StreamSession : historique des diffusions (écrite à la main)."""

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
        ("channels_app", "0002_channel_category"),
    ]

    operations = [
        migrations.CreateModel(
            name="StreamSession",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                ),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("peak_viewers", models.PositiveIntegerField(default=0)),
                ("title_snapshot", models.CharField(blank=True, max_length=140)),
                (
                    "category_snapshot",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="catalog.game",
                    ),
                ),
                (
                    "channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sessions",
                        to="channels_app.channel",
                    ),
                ),
            ],
            options={"ordering": ["-started_at"]},
        ),
    ]
