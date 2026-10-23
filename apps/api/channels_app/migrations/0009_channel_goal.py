"""Objectif de stream (widget OBS « barre d'objectif ») — écrite à la main."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("channels_app", "0008_bunny_stream_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="goal_title",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="channel",
            name="goal_kind",
            field=models.CharField(
                choices=[("subs", "Nouveaux abonnés"), ("tips", "Aura reçue")],
                default="subs",
                max_length=8,
            ),
        ),
        migrations.AddField(
            model_name="channel",
            name="goal_target",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="channel",
            name="goal_started_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
