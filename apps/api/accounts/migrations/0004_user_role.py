"""Rôle utilisateur (user/support/moderator/admin) — écrite à la main."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_user_last_active"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("user", "Utilisateur"),
                    ("support", "Support"),
                    ("moderator", "Modérateur"),
                    ("admin", "Administrateur"),
                ],
                db_index=True,
                default="user",
                max_length=12,
            ),
        ),
    ]
