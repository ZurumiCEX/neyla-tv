"""Données d'icônes SVG (chemins) pour l'admin Neyla.

Fichier de données : les lignes longues (chemins SVG) sont volontaires.
"""

# ruff: noqa: E501

from __future__ import annotations

ICONS: dict[str, str] = {
    "grid": (
        '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>'
    ),
    "users": (
        '<path d="M17 20h5v-2a4 4 0 0 0-3-3.87M9 20H4v-2a4 4 0 0 1 3-3.87'
        'm6-1.13a4 4 0 1 0-4 0M17 7a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/>'
    ),
    "cash": (
        '<rect x="2" y="6" width="20" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/>'
        '<path d="M6 12h.01M18 12h.01"/>'
    ),
    "live": '<circle cx="12" cy="12" r="3"/><path d="M5.5 5.5a9 9 0 0 0 0 13M18.5 5.5a9 9 0 0 1 0 13"/>',
    "shield": '<path d="M12 3 4 6v6c0 5 3.5 7.5 8 9 4.5-1.5 8-4 8-9V6l-8-3Z"/>',
    "play": '<path d="M5 4v16M19 4v16M5 9h14M5 15h14"/>',
    "gift": (
        '<rect x="3" y="8" width="18" height="13" rx="1"/>'
        '<path d="M3 12h18M12 8v13M12 8S9 3 7 5s5 3 5 3 3-5 5-3-5 3-5 3"/>'
    ),
    "cog": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83'
        "l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0"
        "v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83"
        "l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09"
        "a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83"
        "l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09"
        "a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83"
        "l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09"
        'a1.65 1.65 0 0 0-1.51 1Z"/>'
    ),
    "dot": '<circle cx="12" cy="12" r="3.4"/>',
    "heart": (
        '<path d="M19 14c1.5-1.5 3-3.3 3-5.5C22 5.4 19.6 3 16.5 3 14.7 3 13 4 12 5.5'
        '11 4 9.3 3 7.5 3 4.4 3 2 5.4 2 8.5c0 2.2 1.5 4 3 5.5l7 7 7-7Z"/>'
    ),
    "ticket": '<path d="M3 8a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2 2 2 0 0 0 0 4 2 2 0 0 1-2 2H5a2 2 0 0 1-2-2 2 2 0 0 0 0-4Z"/><path d="M13 6v12"/>',
    "video": '<rect x="2" y="6" width="14" height="12" rx="2"/><path d="m16 10 6-3v10l-6-3"/>',
    "game": '<rect x="2" y="7" width="20" height="10" rx="5"/><path d="M7 11v2M6 12h2M16 11h.01M18 13h.01"/>',
    "broadcast": '<circle cx="12" cy="12" r="2.5"/><path d="M5.5 5.5a9 9 0 0 0 0 13M18.5 5.5a9 9 0 0 1 0 13"/>',
    "star": '<path d="m12 3 2.7 5.5 6 .9-4.3 4.2 1 6-5.4-2.8L6.6 19.6l1-6L3.3 9.4l6-.9L12 3Z"/>',
    "wallet": '<rect x="2" y="6" width="20" height="13" rx="2"/><path d="M16 12h4M2 9h18"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "cart": '<circle cx="9" cy="20" r="1.4"/><circle cx="18" cy="20" r="1.4"/><path d="M2 3h3l2.4 12h11l1.6-8H6"/>',
    "percent": '<path d="M19 5 5 19"/><circle cx="7" cy="7" r="2.2"/><circle cx="17" cy="17" r="2.2"/>',
    "repeat": '<path d="M17 2l4 4-4 4M3 11V9a4 4 0 0 1 4-4h14M7 22l-4-4 4-4M21 13v2a4 4 0 0 1-4 4H3"/>',
    "trophy": '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4ZM5 5H3v2a3 3 0 0 0 3 3M19 5h2v2a3 3 0 0 1-3 3"/>',
    "flag": '<path d="M4 21V4M4 4h13l-2 4 2 4H4"/>',
    "ban": '<circle cx="12" cy="12" r="9"/><path d="m5.6 5.6 12.8 12.8"/>',
    "alert": '<path d="M12 3 2 20h20L12 3ZM12 10v4M12 17h.01"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 8-3 8h18s-3-1-3-8M13.7 21a2 2 0 0 1-3.4 0"/>',
    "clipboard": '<rect x="8" y="3" width="8" height="4" rx="1"/><path d="M9 5H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-3"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-5-5L5 21"/>',
    "lock": '<rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5v14Z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "trend": '<path d="m3 17 6-6 4 4 8-8M21 7v6M21 7h-6"/>',
    "pie": '<path d="M12 3v9l7 5A9 9 0 1 0 12 3Z"/><path d="M12 3a9 9 0 0 1 8.5 6H12V3Z"/>',
}
