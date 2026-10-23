"""Vidéos « Instant » (Shorts) et likes — écrite à la main."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("channels_app", "0008_bunny_stream_fields"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Short",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                ),
                ("title", models.CharField(max_length=120)),
                ("video_guid", models.CharField(max_length=64, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("uploading", "Envoi en cours"),
                            ("processing", "Encodage"),
                            ("ready", "Publiée"),
                            ("failed", "Échec"),
                        ],
                        db_index=True,
                        default="uploading",
                        max_length=12,
                    ),
                ),
                ("thumbnail_url", models.URLField(blank=True, max_length=500)),
                ("playback_url", models.URLField(blank=True, max_length=500)),
                ("duration_s", models.PositiveIntegerField(default=0)),
                ("view_count", models.PositiveIntegerField(default=0)),
                ("like_count", models.PositiveIntegerField(default=0)),
                ("is_published", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("published_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                (
                    "channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shorts",
                        to="channels_app.channel",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="short",
            index=models.Index(
                fields=["status", "is_published", "-published_at"],
                name="shorts_feed_idx",
            ),
        ),
        migrations.CreateModel(
            name="ShortLike",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "short",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="likes",
                        to="shorts.short",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="short_likes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="shortlike",
            constraint=models.UniqueConstraint(fields=("user", "short"), name="uniq_short_like"),
        ),
    ]
