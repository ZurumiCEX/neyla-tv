"""Aura dépensée à vie (niveaux) + reprise depuis le grand livre — écrite à la main."""

from django.db import migrations, models
from django.db.models import Sum

SPEND_KINDS = ("tip_sent", "sub_paid", "charity_donation")


def backfill(apps, schema_editor):
    LedgerEntry = apps.get_model("payments", "LedgerEntry")
    User = apps.get_model("accounts", "User")
    totals = (
        LedgerEntry.objects.filter(kind__in=SPEND_KINDS, amount__lt=0)
        .values("wallet__user_id")
        .annotate(total=Sum("amount"))
    )
    for row in totals:
        User.objects.filter(pk=row["wallet__user_id"]).update(
            lifetime_aura_spent=-int(row["total"] or 0)
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0013_user_date_of_birth"),
        ("payments", "0010_revenue_refunds_payout_destination"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="lifetime_aura_spent",
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
