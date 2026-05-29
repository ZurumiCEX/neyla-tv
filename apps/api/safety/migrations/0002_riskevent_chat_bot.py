"""Ajoute le type de risque CHAT_BOT (écrite à la main)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="riskevent",
            name="kind",
            field=models.CharField(
                choices=[
                    ("tip_velocity", "Tips trop rapides"),
                    ("self_deal", "Auto-transaction"),
                    ("follow_velocity", "Follows trop rapides"),
                    ("multi_account", "Multi-comptes (IP partagée)"),
                    ("view_inflation", "Gonflage de vues"),
                    ("sub_abuse", "Abus d'abonnement"),
                    ("chat_bot", "Bot de chat"),
                ],
                db_index=True,
                max_length=24,
            ),
        ),
    ]
