"""Réglages du chat par chaîne (accès, options, modération auto) — écrite à la main."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("channels_app", "0009_channel_goal")]

    operations = [
        migrations.AddField(
            model_name="channel",
            name="chat_followers_only",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="channel",
            name="chat_follow_min_minutes",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="channel",
            name="chat_subscribers_only",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="channel",
            name="chat_emotes_only",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="channel",
            name="chat_slow_seconds",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="channel",
            name="chat_min_account_age_days",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="channel",
            name="show_viewer_count",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="channel",
            name="automod",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
