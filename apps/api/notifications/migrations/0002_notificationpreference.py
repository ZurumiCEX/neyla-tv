"""Préférences de notification par type — écrite à la main."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("live_started", "Live démarré"),
                            ("new_follower", "Nouveau follower"),
                            ("application_decided", "Candidature traitée"),
                            ("subscription", "Nouvel abonné"),
                            ("tip_received", "Tip reçu"),
                            ("achievement", "Succès débloqué"),
                            ("support_message", "Message du support"),
                        ],
                        max_length=32,
                    ),
                ),
                ("enabled", models.BooleanField(default=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notification_prefs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="notificationpreference",
            constraint=models.UniqueConstraint(fields=["user", "type"], name="uniq_notif_pref"),
        ),
    ]
