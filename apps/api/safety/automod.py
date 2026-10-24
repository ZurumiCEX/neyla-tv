"""Modération automatique du chat, réglée par chaîne (dashboard → Modération).

Chaque catégorie a un niveau 0 (non filtré) → 3 (maximum). Les termes du
lexique ont une gravité 1 (léger) → 3 (grave) : au niveau N, un terme est
bloqué si sa gravité ≥ 4 − N (minimal = graves seulement, maximum = tout).
Filtres complémentaires : charabia (« gibberish ») et spam (liens, e-mails,
téléphones). Pas d'appel réseau : simple, rapide, explicable.
"""

from __future__ import annotations

import re
import unicodedata

CATEGORIES = ("sexual", "hate", "violence", "bullying", "drugs", "weapons")

# Lexiques FR / EN / nouchi courants (gravité 1 → 3). Volontairement courts :
# les streamers complètent avec leurs mots interdits.
LEXICON: dict[str, dict[str, int]] = {
    "sexual": {
        "porn": 3,
        "porno": 3,
        "xxx": 3,
        "nudes": 3,
        "nude": 2,
        "sexe": 2,
        "sex": 2,
        "boobs": 2,
        "seins": 1,
        "sexy": 1,
        "onlyfans": 2,
    },
    "hate": {
        "nazi": 3,
        "heil": 3,
        "sale race": 3,
        "raciste": 1,
        "go back to africa": 3,
        "retourne dans ton pays": 3,
        "macaque": 3,
        "singe": 2,
    },
    "violence": {
        "je vais te tuer": 3,
        "i will kill you": 3,
        "kill yourself": 3,
        "kys": 3,
        "suicide toi": 3,
        "egorger": 3,
        "massacre": 2,
        "tuer": 2,
        "kill": 2,
        "buter": 2,
        "frapper": 1,
    },
    "bullying": {
        "connard": 3,
        "connasse": 3,
        "fdp": 3,
        "ntm": 3,
        "pute": 3,
        "salope": 3,
        "batard": 2,
        "abruti": 2,
        "debile": 2,
        "loser": 1,
        "idiot": 1,
        "nul": 1,
        "stupide": 1,
    },
    "drugs": {
        "cocaine": 3,
        "heroine": 3,
        "heroin": 3,
        "crack": 2,
        "meth": 3,
        "beuh": 2,
        "weed": 2,
        "cannabis": 2,
        "shit": 1,
        "joint": 1,
    },
    "weapons": {
        "kalash": 3,
        "ak47": 3,
        "grenade": 2,
        "fusil": 2,
        "pistolet": 2,
        "gun": 2,
        "flingue": 2,
        "couteau": 1,
        "machette": 2,
    },
}

PRESETS = {
    "unfiltered": dict.fromkeys(CATEGORIES, 0),
    "minimal": dict.fromkeys(CATEGORIES, 1),
    "moderate": dict.fromkeys(CATEGORIES, 2),
    "maximum": dict.fromkeys(CATEGORIES, 3),
}

_URL = re.compile(r"(https?://|www\.)\S+|\b[\w-]+\.(com|net|org|io|gg|tv|fr|ly|me|xyz)\b", re.I)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_PHONE = re.compile(r"(?:\+?\d[\s.-]?){8,}")
_REPEAT = re.compile(r"(.)\1{6,}")
_VOWELS = set("aeiouy")


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text)


def normalize_settings(raw: dict | None) -> dict:
    """Réglages complets et bornés à partir de ce qui est stocké sur la chaîne."""
    raw = raw or {}
    out = {cat: max(0, min(3, int(raw.get(cat, 0) or 0))) for cat in CATEGORIES}
    out["gibberish"] = bool(raw.get("gibberish", False))
    out["spam"] = bool(raw.get("spam", False))
    return out


def _is_gibberish(text: str) -> bool:
    if _REPEAT.search(text):
        return True
    for token in re.findall(r"[a-z]{8,}", text):
        vowels = sum(1 for c in token if c in _VOWELS)
        if vowels == 0 or vowels / len(token) < 0.15:
            return True
    return False


def check(text: str, settings: dict | None) -> str | None:
    """Renvoie la catégorie qui bloque le message, ou None s'il passe."""
    conf = normalize_settings(settings)
    norm = _normalize(text)
    padded = f" {re.sub(r'[^a-z0-9 ]', ' ', norm)} "
    for cat in CATEGORIES:
        level = conf[cat]
        if level == 0:
            continue
        threshold = 4 - level
        for term, severity in LEXICON[cat].items():
            if severity >= threshold and f" {term} " in padded:
                return cat
    if conf["spam"] and (_URL.search(text) or _EMAIL.search(text) or _PHONE.search(text)):
        return "spam"
    if conf["gibberish"] and _is_gibberish(norm):
        return "gibberish"
    return None
