"""Module Charity Day (écrite à la main)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Charity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("description", models.TextField(blank=True)),
                ("country", models.CharField(blank=True, max_length=2)),
                ("logo_url", models.URLField(blank=True)),
                ("website_url", models.URLField(blank=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
                "verbose_name": "Association",
                "verbose_name_plural": "Associations",
            },
        ),
        migrations.CreateModel(
            name="CharityEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("title", models.CharField(max_length=140)),
                ("theme", models.CharField(blank=True, max_length=80)),
                ("description_md", models.TextField(blank=True)),
                ("cover_url", models.URLField(blank=True)),
                ("starts_at", models.DateTimeField(db_index=True)),
                ("ends_at", models.DateTimeField(db_index=True)),
                ("floor_aura", models.PositiveIntegerField(default=10)),
                ("is_published", models.BooleanField(db_index=True, default=True)),
                ("total_aura_cached", models.PositiveBigIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "beneficiaries",
                    models.ManyToManyField(related_name="events", to="charity.charity"),
                ),
            ],
            options={
                "ordering": ["-starts_at"],
                "verbose_name": "Charity Day",
                "verbose_name_plural": "Charity Days",
            },
        ),
        migrations.CreateModel(
            name="CharityDonation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("aura_amount", models.PositiveIntegerField()),
                ("message", models.CharField(blank=True, max_length=140)),
                ("is_anonymous", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "charity",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="donations",
                        to="charity.charity",
                    ),
                ),
                (
                    "donor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="charity_donations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="donations",
                        to="charity.charityevent",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="charitydonation",
            index=models.Index(fields=["event", "-aura_amount"], name="charity_event_lb_idx"),
        ),
    ]
