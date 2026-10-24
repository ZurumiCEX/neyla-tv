"""Niveaux (Aura dépensée à vie) et badges de don (total offert à une chaîne)."""

from __future__ import annotations

# (seuil d'Aura dépensée, clé). En dessous du premier seuil : « rookie ».
LEVELS: list[tuple[int, str]] = [
    (10_000, "beginner"),
    (50_000, "casual"),
    (100_000, "great"),
    (200_000, "lord"),
    (500_000, "mvp"),
    (1_000_000, "goat"),
]
ROOKIE = "rookie"

# Badges de don par chaîne : 1 · 100 · 1 000 · 5 000 · 10 000 Aura offerts.
GIFT_TIERS: list[tuple[int, str]] = [
    (1, "spark"),
    (100, "glow"),
    (1_000, "radiant"),
    (5_000, "nova"),
    (10_000, "supreme"),
]


def level_for(spent: int) -> str:
    key = ROOKIE
    for threshold, name in LEVELS:
        if spent >= threshold:
            key = name
    return key


def level_progress(spent: int) -> dict:
    """Niveau actuel, suivant et progression en % vers le suivant."""
    spent = max(0, int(spent))
    current = level_for(spent)
    floor = next((t for t, k in LEVELS if k == current), 0)
    nxt = next(((t, k) for t, k in LEVELS if spent < t), None)
    pct = 100 if nxt is None else int((spent - floor) * 100 / max(1, nxt[0] - floor))
    return {
        "level": current,
        "next_level": nxt[1] if nxt else None,
        "next_at": nxt[0] if nxt else None,
        "progress": max(0, min(100, pct)),
    }


def gift_tier(total: int) -> str | None:
    key = None
    for threshold, name in GIFT_TIERS:
        if total >= threshold:
            key = name
    return key
