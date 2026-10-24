"""Mots interdits par chaîne, journal de modération, demandes de déban — écrite à la main."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0003_chatipban_chatuserip"),
        ("channels_app", "0010_channel_chat_settings"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ChannelBannedWord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("word", models.CharField(max_length=60)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="banned_words",
                        to="channels_app.channel",
                    ),
                ),
            ],
            options={"ordering": ["word"]},
        ),
        migrations.AddConstraint(
            model_name="channelbannedword",
            constraint=models.UniqueConstraint(
                fields=("channel", "word"), name="uniq_channel_banned_word"
            ),
        ),
        migrations.CreateModel(
            name="ModAction",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("ban", "Ban"),
                            ("timeout", "Timeout"),
                            ("unban", "Unban"),
                            ("shadow", "Shadow ban"),
                            ("unshadow", "Fin du shadow ban"),
                            ("ipban", "Ban IP"),
                            ("ipunban", "Fin du ban IP"),
                            ("delete", "Message supprimé"),
                            ("slowmode", "Slow mode"),
                            ("automod", "Message bloqué (auto)"),
                            ("settings", "Réglages du chat"),
                        ],
                        max_length=12,
                    ),
                ),
                ("duration_s", models.PositiveIntegerField(default=0)),
                ("detail", models.CharField(blank=True, max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mod_actions",
                        to="channels_app.channel",
                    ),
                ),
                (
                    "target_user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="modaction",
            index=models.Index(fields=["channel", "-created_at"], name="modaction_channel_idx"),
        ),
        migrations.CreateModel(
            name="UnbanRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("message", models.CharField(max_length=500)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("approved", "Acceptée"),
                            ("denied", "Refusée"),
                        ],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("decided_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="unban_requests",
                        to="channels_app.channel",
                    ),
                ),
                (
                    "decided_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="unban_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="unbanrequest",
            index=models.Index(fields=["channel", "status"], name="unban_channel_status_idx"),
        ),
    ]
