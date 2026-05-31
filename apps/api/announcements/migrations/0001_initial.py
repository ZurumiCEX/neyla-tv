"""Annonces site (écrite à la main)."""

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    operations = [
        migrations.CreateModel(
            name="SiteAnnouncement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=140)),
                ("body", models.TextField(blank=True)),
                (
                    "level",
                    models.CharField(
                        choices=[
                            ("info", "Info"),
                            ("success", "Succès"),
                            ("warning", "Avertissement"),
                            ("critical", "Critique"),
                        ],
                        default="info",
                        max_length=10,
                    ),
                ),
                (
                    "display_mode",
                    models.CharField(
                        choices=[
                            ("ticker", "Ticker (défilant sous le header)"),
                            ("popup", "Pop-up (une fois par utilisateur)"),
                            ("both", "Ticker + pop-up"),
                        ],
                        default="ticker",
                        max_length=10,
                    ),
                ),
                (
                    "audience",
                    models.CharField(
                        choices=[
                            ("all", "Tous"),
                            ("streamers", "Streamers"),
                            ("viewers", "Spectateurs (non streamers)"),
                            ("anonymous", "Visiteurs anonymes"),
                        ],
                        db_index=True,
                        default="all",
                        max_length=10,
                    ),
                ),
                (
                    "starts_at",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now),
                ),
                ("ends_at", models.DateTimeField(db_index=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("dismissible", models.BooleanField(default=True)),
                ("cta_label", models.CharField(blank=True, max_length=40)),
                ("cta_url", models.URLField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-starts_at"],
                "verbose_name": "Annonce site",
                "verbose_name_plural": "Annonces site",
            },
        ),
    ]
