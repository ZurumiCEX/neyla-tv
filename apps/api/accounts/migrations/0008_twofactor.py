"""Configuration 2FA (TOTP) par utilisateur (écrite à la main)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0007_usersession"),
    ]

    operations = [
        migrations.CreateModel(
            name="TwoFactor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("secret", models.CharField(max_length=64)),
                ("enabled", models.BooleanField(default=False)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("recovery_codes", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="two_factor",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
