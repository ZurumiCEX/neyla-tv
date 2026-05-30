"""Scoring automatique d'une candidature streamer (signaux forts → priorisation).

Barème (max 100) :
- Expérience streaming (a déjà streamé)        +20
- Communauté existante (selon le palier)       +25
- Bonne motivation (longueur/qualité du texte) +20
- Fréquence élevée prévue                       +15
- Setup correct                                 +10
- Réseaux sociaux actifs                        +10
"""

from __future__ import annotations

_COMMUNITY_PTS = {
    "none": 0,
    "under_100": 8,
    "100_1k": 15,
    "1k_10k": 22,
    "10k_plus": 25,
}
_FREQUENCY_PTS = {
    "occasional": 3,
    "1_2_week": 8,
    "3_5_week": 12,
    "daily": 15,
}
_SETUP_KEYS = {"pc", "console", "mobile", "webcam", "microphone", "stable_net"}


def compute_score(application) -> int:
    score = 0

    # Expérience streaming
    if application.has_streamed:
        score += 20

    # Communauté existante
    score += _COMMUNITY_PTS.get(application.community_size, 0)

    # Qualité de la motivation (motivation + signaux forts)
    text = " ".join(
        filter(
            None,
            [application.motivation, application.why_select, application.what_bring],
        )
    ).strip()
    n = len(text)
    if n >= 400:
        score += 20
    elif n >= 200:
        score += 14
    elif n >= 80:
        score += 8

    # Fréquence prévue
    score += _FREQUENCY_PTS.get(application.frequency, 0)

    # Setup
    setup = [s for s in (application.setup or []) if s in _SETUP_KEYS]
    if len(setup) >= 3:
        score += 10
    elif setup:
        score += 5

    # Réseaux sociaux actifs (jusqu'à 2 → 10 pts)
    active_socials = sum(1 for v in (application.platforms or {}).values() if v)
    score += min(active_socials, 2) * 5

    return min(score, 100)
