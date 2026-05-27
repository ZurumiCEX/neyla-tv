"""last_active_at sur User (analytics DAU/MAU) — écrite à la main."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_user_profile_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="last_active_at",
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
