"""Achievement enrichi : criteria, icon_url, is_active (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gamification", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="achievement",
            name="criteria",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="achievement",
            name="icon_url",
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name="achievement",
            name="is_active",
            field=models.BooleanField(default=True, db_index=True),
        ),
        migrations.AlterField(
            model_name="achievement",
            name="description",
            field=models.CharField(blank=True, max_length=300),
        ),
    ]
