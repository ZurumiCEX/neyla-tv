"""Creator Application System : champs détaillés + scoring + états (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("streamers", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="streamerapplication",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "En attente"),
                    ("under_review", "En cours d'examen"),
                    ("interview", "Entretien demandé"),
                    ("approved", "Approuvée"),
                    ("rejected", "Rejetée"),
                ],
                db_index=True,
                default="pending",
                max_length=14,
            ),
        ),
        migrations.AlterField(
            model_name="streamerapplication",
            name="motivation",
            field=models.TextField(blank=True, max_length=2000),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="full_name",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="country",
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="primary_language",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="main_games",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="content_categories",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="goals",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="community_type",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="has_streamed",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="platforms",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="community_size",
            field=models.CharField(blank=True, max_length=12),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="frequency",
            field=models.CharField(blank=True, max_length=12),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="avg_duration",
            field=models.CharField(blank=True, max_length=12),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="setup",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="connection_quality",
            field=models.CharField(blank=True, max_length=12),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="why_select",
            field=models.TextField(blank=True, max_length=1000),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="what_bring",
            field=models.TextField(blank=True, max_length=1000),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="intro_video_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="setup_screenshot_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="rules_accepted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="score",
            field=models.PositiveIntegerField(db_index=True, default=0),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="admin_notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="tags",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="streamerapplication",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterModelOptions(
            name="streamerapplication",
            options={"ordering": ["-score", "-created_at"]},
        ),
    ]
