"""Type « abonnement offert » (séparé de « nouvel abonné ») — écrite à la main."""

from django.db import migrations, models

CHOICES = [
    ("live_started", "Live démarré"),
    ("new_follower", "Nouveau follower"),
    ("application_decided", "Candidature traitée"),
    ("subscription", "Nouvel abonné"),
    ("subscription_gift", "Abonnement offert"),
    ("tip_received", "Tip reçu"),
    ("achievement", "Succès débloqué"),
    ("support_message", "Message du support"),
]


class Migration(migrations.Migration):
    dependencies = [("notifications", "0003_pushsubscription")]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="type",
            field=models.CharField(choices=CHOICES, max_length=32),
        ),
        migrations.AlterField(
            model_name="notificationpreference",
            name="type",
            field=models.CharField(choices=CHOICES, max_length=32),
        ),
    ]
