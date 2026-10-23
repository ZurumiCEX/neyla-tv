"""Prix verrouillé, annulation en fin de période, renouvellement auto (écrite à la main).

Données : `price_paid` reprend le prix actuel du palier ; les abonnements déjà
annulés mais encore dans leur période redeviennent actifs avec
`cancel_at_period_end` (l'accès payé n'est plus coupé à l'annulation) ; les
abonnements offerts ne se renouvellent plus.
"""

from django.db import migrations, models
from django.utils import timezone


def forwards(apps, schema_editor):
    Subscription = apps.get_model("subscriptions", "Subscription")
    for sub in Subscription.objects.select_related("tier").iterator():
        sub.price_paid = sub.tier.price_aura if sub.tier_id else 0
        if sub.gifted_by_id:
            sub.auto_renew = False
        if sub.status == "canceled" and sub.current_period_end > timezone.now():
            sub.status = "active"
            sub.cancel_at_period_end = True
        sub.save(update_fields=["price_paid", "auto_renew", "status", "cancel_at_period_end"])


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0003_subtier_badge_stickers"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="price_paid",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="subscription",
            name="cancel_at_period_end",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="subscription",
            name="auto_renew",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
