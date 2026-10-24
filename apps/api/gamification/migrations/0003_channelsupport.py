"""Badges de don : total offert par follower et par chaîne — écrite à la main.

Reprise depuis les tips existants (les abonnements offerts passés ne sont pas
historisés : ils comptent à partir de maintenant).
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.db.models import Max, Sum


def backfill(apps, schema_editor):
    Tip = apps.get_model("payments", "Tip")
    ChannelSupport = apps.get_model("gamification", "ChannelSupport")
    rows = Tip.objects.values("from_user_id", "to_channel_id").annotate(
        total=Sum("aura_amount"), last=Max("created_at")
    )
    ChannelSupport.objects.bulk_create(
        [
            ChannelSupport(
                user_id=r["from_user_id"],
                channel_id=r["to_channel_id"],
                total_aura=r["total"] or 0,
                last_gift_at=r["last"],
            )
            for r in rows
        ],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("gamification", "0002_achievement_richer"),
        ("channels_app", "0009_channel_goal"),
        ("payments", "0010_revenue_refunds_payout_destination"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ChannelSupport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("total_aura", models.PositiveBigIntegerField(default=0)),
                ("last_gift_at", models.DateTimeField(blank=True, null=True)),
                (
                    "channel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="supporters",
                        to="channels_app.channel",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="channel_supports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-total_aura"]},
        ),
        migrations.AddConstraint(
            model_name="channelsupport",
            constraint=models.UniqueConstraint(
                fields=("user", "channel"), name="uniq_channel_support"
            ),
        ),
        migrations.AddIndex(
            model_name="channelsupport",
            index=models.Index(fields=["channel", "-total_aura"], name="support_channel_total_idx"),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
