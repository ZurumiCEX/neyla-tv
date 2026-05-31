"""Calendrier d'événements de plateforme (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("charity", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlatformEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("title", models.CharField(max_length=140)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("charity", "Charity Day"),
                            ("tournament", "Tournoi"),
                            ("premiere", "Première"),
                            ("announcement", "Annonce"),
                            ("maintenance", "Maintenance"),
                        ],
                        db_index=True,
                        default="announcement",
                        max_length=20,
                    ),
                ),
                ("description_md", models.TextField(blank=True)),
                ("cover_url", models.URLField(blank=True)),
                ("link_url", models.URLField(blank=True)),
                ("starts_at", models.DateTimeField(db_index=True)),
                ("ends_at", models.DateTimeField(db_index=True)),
                ("is_published", models.BooleanField(db_index=True, default=True)),
                ("featured", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["starts_at"],
                "verbose_name": "Événement plateforme",
                "verbose_name_plural": "Événements plateforme",
            },
        ),
    ]
