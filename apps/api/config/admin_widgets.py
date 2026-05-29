"""Widgets HTML/SVG réutilisables pour l'admin (synthèses en lecture seule).

Le contenu est construit uniquement à partir de valeurs internes (nombres,
libellés littéraux, couleurs) — aucune donnée utilisateur n'y est interpolée,
d'où les ``# noqa: S308`` sur les ``mark_safe``.
"""

from __future__ import annotations

from django.utils.safestring import mark_safe


def svg_area(values: list[float], color: str, w: int = 260, h: int = 48) -> str:
    """Mini graphe (aire + ligne) SVG inline, sans dépendance front."""
    n = len(values)
    if n == 0:
        return ""
    vmax = max(values) or 1
    vmin = min(values + [0])
    rng = (vmax - vmin) or 1
    pad = 4

    def x(i: int) -> float:
        return pad + (i / (n - 1) * (w - 2 * pad) if n > 1 else (w - 2 * pad) / 2)

    def y(v: float) -> float:
        return h - pad - (v - vmin) / rng * (h - 2 * pad)

    line = " ".join(f"{'M' if i == 0 else 'L'}{x(i):.1f} {y(v):.1f}" for i, v in enumerate(values))
    area = f"{line} L{x(n - 1):.1f} {h} L{x(0):.1f} {h} Z"
    return (
        f'<svg viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
        f'style="width:100%;max-width:{w}px;height:{h}px">'
        f'<path d="{area}" fill="{color}" opacity="0.18"/>'
        f'<path d="{line}" fill="none" stroke="{color}" stroke-width="2" '
        f'vector-effect="non-scaling-stroke"/></svg>'
    )


def stat_grid(items: list[tuple[str, object]]) -> str:
    """Grille de statistiques (valeur + libellé) en lecture seule."""
    cells = "".join(
        f'<div style="min-width:110px">'
        f'<div style="font-size:18px;font-weight:700;line-height:1.1">{v}</div>'
        f'<div style="font-size:11px;color:#666;text-transform:uppercase;'
        f'letter-spacing:.03em;margin-top:2px">{label}</div></div>'
        for label, v in items
    )
    return mark_safe(  # noqa: S308 — libellés littéraux + valeurs numériques internes
        f'<div style="display:flex;gap:22px;flex-wrap:wrap;align-items:flex-end">{cells}</div>'
    )


def labeled_chart(title: str, values: list[float], color: str) -> str:
    """Graphe SVG précédé d'un petit titre."""
    return mark_safe(  # noqa: S308 — voir docstring du module
        f'<div style="margin-top:6px"><div style="font-size:11px;color:#666;'
        f'margin-bottom:4px">{title}</div>{svg_area(values, color)}</div>'
    )
