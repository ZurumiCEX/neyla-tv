"""Shadow ban sur ChatBan (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatban",
            name="shadow",
            field=models.BooleanField(default=False),
        ),
    ]
