"""Classificateur de contenu (anti-violation).

Abstraction à deux backends :
- HEURISTIC (défaut) : lexique de mots-clés FR/EN pour le TEXTE. Les images ne
  peuvent pas être analysées sans modèle de vision → renvoyées "unknown"
  (mises en file d'examen si SAFETY_REVIEW_UPLOADS=on).
- Fournisseur de vision externe (Sightengine / AWS Rekognition / Hive…) : à
  brancher via `SAFETY_VISION_PROVIDER`. Interface `classify_image(url)`.

Le reste du module (ContentFlag, auto-actions, file de modération) est agnostique
du backend.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from django.conf import settings

# Lexiques volontairement sobres (termes explicites). Catégorie → mots-clés.
_SEXUAL = {
    "porn",
    "porno",
    "pornographie",
    "xxx",
    "nude",
    "nudes",
    "naked",
    "sexe",
    "sexcam",
    "camgirl",
    "onlyfans",
    "escort",
    "fellation",
    "masturbation",
}
_GORE = {
    "gore",
    "decapitation",
    "décapitation",
    "beheading",
    "snuff",
    "mutilation",
    "torture",
    "dismemberment",
    "égorgement",
}


@dataclass
class ScanResult:
    category: str  # "safe" | "sexual" | "gore" | "other" | "unknown"
    confidence: float = 0.0
    scores: dict = field(default_factory=dict)

    @property
    def is_violation(self) -> bool:
        return self.category in ("sexual", "gore")


def _normalize(text: str) -> str:
    return (text or "").lower()


def classify_text(text: str) -> ScanResult:
    """Heuristique lexicale : repère termes sexuels / gore explicites."""
    blob = _normalize(text)
    if not blob:
        return ScanResult("safe", 0.0)
    tokens = set(blob.replace("/", " ").replace(",", " ").split())
    sexual_hits = sorted(tokens & _SEXUAL)
    gore_hits = sorted(tokens & _GORE)
    # Mots interdits configurés par la modération (réutilise l'existant).
    extra_hits: list[str] = []
    try:
        from moderation.services import get_banned_words

        banned = get_banned_words()
        extra_hits = [w for w in banned if w and w in blob]
    except Exception:  # noqa: BLE001
        extra_hits = []

    if sexual_hits:
        return ScanResult("sexual", 0.9, {"matches": sexual_hits})
    if gore_hits:
        return ScanResult("gore", 0.9, {"matches": gore_hits})
    if extra_hits:
        return ScanResult("other", 0.6, {"matches": extra_hits})
    return ScanResult("safe", 0.0)


def classify_image(url: str) -> ScanResult:
    """Analyse d'image. Sans fournisseur de vision configuré → "unknown"."""
    provider = getattr(settings, "SAFETY_VISION_PROVIDER", "")
    if not provider:
        return ScanResult("unknown", 0.0, {"reason": "no_vision_provider"})
    # Point d'extension : appeler ici l'API de vision retenue et mapper la réponse.
    raise NotImplementedError(f"Fournisseur de vision '{provider}' déclaré mais non implémenté.")
