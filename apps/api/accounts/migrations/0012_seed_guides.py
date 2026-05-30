"""Peuple les guides par défaut (idempotent). Réversible (no-op au rollback)."""

from django.db import migrations


def seed_guides(apps, schema_editor):
    from accounts.guides_seed import GUIDES_SEED

    Guide = apps.get_model("accounts", "Guide")
    GuideStep = apps.get_model("accounts", "GuideStep")

    for g in GUIDES_SEED:
        guide, _ = Guide.objects.update_or_create(
            slug=g["slug"],
            defaults={
                "icon": g["icon"],
                "order": g["order"],
                "is_published": True,
                "title_fr": g["title"]["fr"],
                "title_en": g["title"]["en"],
                "title_pt": g["title"]["pt"],
                "desc_fr": g["desc"]["fr"],
                "desc_en": g["desc"]["en"],
                "desc_pt": g["desc"]["pt"],
            },
        )
        for i, s in enumerate(g["steps"]):
            GuideStep.objects.update_or_create(
                guide=guide,
                step_id=s["step_id"],
                defaults={
                    "order": i,
                    "title_fr": s["title"]["fr"],
                    "title_en": s["title"]["en"],
                    "title_pt": s["title"]["pt"],
                    "body_fr": s["body"]["fr"],
                    "body_en": s["body"]["en"],
                    "body_pt": s["body"]["pt"],
                },
            )


def unseed(apps, schema_editor):
    # Rollback : on ne supprime pas le contenu (peut avoir été édité). No-op.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0011_guide_models"),
    ]

    operations = [migrations.RunPython(seed_guides, unseed)]
