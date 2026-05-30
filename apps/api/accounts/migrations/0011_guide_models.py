"""Guides/tutoriels gérés en base : modèles Guide + GuideStep (écrite à la main)."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0010_terms_accepted"),
    ]

    operations = [
        migrations.CreateModel(
            name="Guide",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("slug", models.SlugField(max_length=60, unique=True)),
                (
                    "icon",
                    models.CharField(
                        choices=[
                            ("rocket", "Fusée"),
                            ("broadcast", "Diffusion"),
                            ("coins", "Pièces"),
                            ("shield", "Bouclier"),
                        ],
                        default="rocket",
                        max_length=20,
                    ),
                ),
                ("order", models.PositiveIntegerField(db_index=True, default=0)),
                ("is_published", models.BooleanField(db_index=True, default=True)),
                ("title_fr", models.CharField(max_length=120)),
                ("title_en", models.CharField(blank=True, max_length=120)),
                ("title_pt", models.CharField(blank=True, max_length=120)),
                ("desc_fr", models.CharField(blank=True, max_length=300)),
                ("desc_en", models.CharField(blank=True, max_length=300)),
                ("desc_pt", models.CharField(blank=True, max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.CreateModel(
            name="GuideStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("step_id", models.SlugField(max_length=60)),
                ("order", models.PositiveIntegerField(db_index=True, default=0)),
                ("title_fr", models.CharField(max_length=160)),
                ("title_en", models.CharField(blank=True, max_length=160)),
                ("title_pt", models.CharField(blank=True, max_length=160)),
                ("body_fr", models.TextField(blank=True)),
                ("body_en", models.TextField(blank=True)),
                ("body_pt", models.TextField(blank=True)),
                (
                    "guide",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="steps",
                        to="accounts.guide",
                    ),
                ),
            ],
            options={"ordering": ["order", "id"]},
        ),
        migrations.AddConstraint(
            model_name="guidestep",
            constraint=models.UniqueConstraint(fields=["guide", "step_id"], name="uniq_guide_step"),
        ),
    ]
