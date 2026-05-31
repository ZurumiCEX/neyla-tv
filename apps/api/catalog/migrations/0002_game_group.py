"""Ajoute le champ `group` (Jeux/IRL/Discussions/Musique/Créativité) sur Game.

Assigne par défaut `games` à toutes les lignes existantes, sauf quelques slugs
connus qui sont reclassés explicitement (just-chatting → chatting).
"""

from __future__ import annotations

from django.db import migrations, models

_RECLASSIFY = {
    "just-chatting": "chatting",
}


def reclassify(apps, schema_editor):
    Game = apps.get_model("catalog", "Game")
    for slug, group in _RECLASSIFY.items():
        Game.objects.filter(slug=slug).update(group=group)


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="game",
            name="group",
            field=models.CharField(
                choices=[
                    ("games", "Jeux"),
                    ("irl", "IRL"),
                    ("chatting", "Discussions"),
                    ("music", "Musique"),
                    ("creative", "Créativité"),
                ],
                db_index=True,
                default="games",
                max_length=16,
            ),
        ),
        migrations.RunPython(reclassify, noop),
    ]
