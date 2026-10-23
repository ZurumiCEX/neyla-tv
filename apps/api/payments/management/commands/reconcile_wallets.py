"""Contrôle de cohérence : solde des wallets == somme de leur grand livre.

python manage.py reconcile_wallets          # rapport (code de sortie 1 si écart)
"""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from payments.services import wallet_drift


class Command(BaseCommand):
    help = "Vérifie que chaque solde Aura correspond à la somme de son grand livre."

    def handle(self, *args, **options):
        drift = wallet_drift()
        if not drift:
            ok = "✓ Tous les wallets sont cohérents avec le ledger."
            self.stdout.write(self.style.SUCCESS(ok))
            return
        for row in drift:
            self.stdout.write(
                self.style.ERROR(
                    f"@{row['user']} : solde {row['balance']} ≠ ledger {row['ledger_sum']} "
                    f"(écart {row['delta']:+d})"
                )
            )
        raise CommandError(f"{len(drift)} wallet(s) incohérent(s).")
