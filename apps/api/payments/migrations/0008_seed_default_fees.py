"""Règles de commission par défaut (business model plateforme).

- Tip 30% — Abonnement 30% — Achat 1% (sur streamers uniquement, géré dans
  ``confirm_purchase``).

Idempotent : si une règle ACTIVE existe déjà pour un produit, on ne touche à rien.
"""

from django.db import migrations


def seed_fees(apps, schema_editor):
    FeeRule = apps.get_model("payments", "FeeRule")
    defaults = [
        ("tip", "percentage", 30),
        ("subscription", "percentage", 30),
        ("purchase", "percentage", 1),
    ]
    for product, mode, value in defaults:
        if not FeeRule.objects.filter(product=product, is_active=True).exists():
            FeeRule.objects.create(product=product, mode=mode, value=value, is_active=True)


def unseed(apps, schema_editor):
    # Rollback : on ne supprime pas (les règles peuvent avoir été modifiées par l'admin).
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("payments", "0007_ledger_adjustment"),
    ]

    operations = [migrations.RunPython(seed_fees, unseed)]
