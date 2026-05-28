"""Ban IP + tracking de la dernière IP par utilisateur (écrite à la main)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0002_chatban_shadow"),
        ("channels_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatIpBan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("ip", models.GenericIPAddressField()),
                ("until", models.DateTimeField(blank=True, null=True)),
                ("reason", models.CharField(blank=True, max_length=200)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chat_ip_bans",
                        to="channels_app.channel",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="chat_ip_bans_issued",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ChatUserIp",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("ip", models.GenericIPAddressField()),
                ("seen_at", models.DateTimeField(auto_now=True)),
                (
                    "channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chat_user_ips",
                        to="channels_app.channel",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chat_user_ips",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="chatipban",
            index=models.Index(fields=["channel", "ip"], name="chat_chatip_channel_idx"),
        ),
        migrations.AddConstraint(
            model_name="chatipban",
            constraint=models.UniqueConstraint(
                fields=["channel", "ip"], name="uniq_chatipban_per_channel_ip"
            ),
        ),
        migrations.AddConstraint(
            model_name="chatuserip",
            constraint=models.UniqueConstraint(
                fields=["channel", "user"], name="uniq_chatuserip_per_channel_user"
            ),
        ),
    ]
