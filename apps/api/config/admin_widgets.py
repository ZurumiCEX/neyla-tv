"""Widgets HTML/SVG réutilisables pour l'admin (synthèses en lecture seule).

Le contenu est construit uniquement à partir de valeurs internes (nombres,
libellés littéraux, couleurs) — aucune donnée utilisateur n'y est interpolée,
d'où les ``# noqa: S308`` sur les ``mark_safe``.
"""

from __future__ import annotations

import math

from django.utils.html import escape
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


def svg_donut(parts: list[tuple[str, float, str]], size: int = 132, thickness: int = 18) -> str:
    """Anneau de répartition. ``parts`` = [(label, valeur, couleur)]."""
    total = sum(max(0, v) for _, v, _ in parts)
    r = (size - thickness) / 2
    c = size / 2
    circ = 2 * math.pi * r
    segs = []
    if total > 0:
        offset = 0.0
        for _label, val, color in parts:
            dash = max(0, val) / total * circ
            segs.append(
                f'<circle cx="{c}" cy="{c}" r="{r:.1f}" fill="none" stroke="{color}" '
                f'stroke-width="{thickness}" stroke-dasharray="{dash:.2f} {circ - dash:.2f}" '
                f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {c} {c})"/>'
            )
            offset += dash
    else:
        segs.append(
            f'<circle cx="{c}" cy="{c}" r="{r:.1f}" fill="none" stroke="#23252e" '
            f'stroke-width="{thickness}"/>'
        )
    return mark_safe(  # noqa: S308 — géométrie interne, valeurs numériques + couleurs littérales
        f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}">{"".join(segs)}</svg>'
    )


def svg_hbars(items: list[tuple[str, float]], color: str, w: int = 300, bar_h: int = 22) -> str:
    """Barres horizontales étiquetées. Les libellés (ex. pseudos) sont échappés."""
    gap = 11
    maxv = max((v for _, v in items), default=0) or 1
    h = max(1, len(items)) * (bar_h + gap)
    out = []
    for i, (label, val) in enumerate(items):
        y = i * (bar_h + gap)
        bw = (max(0, val) / maxv) * (w * 0.6)
        out.append(f'<rect x="0" y="{y}" width="{w}" height="{bar_h}" rx="6" fill="#1b1d26"/>')
        out.append(
            f'<rect x="0" y="{y}" width="{bw:.1f}" height="{bar_h}" rx="6" '
            f'fill="{color}" opacity="0.85"/>'
        )
        ty = y + bar_h * 0.68
        out.append(
            f'<text x="10" y="{ty:.0f}" fill="#e7e9ee" font-size="12">{escape(label)}</text>'
        )
        out.append(
            f'<text x="{w}" y="{ty:.0f}" fill="#9aa3b2" font-size="12" '
            f'text-anchor="end">{escape(str(val))}</text>'
        )
    return mark_safe(  # noqa: S308 — libellés échappés, reste numérique/littéral
        f'<svg viewBox="0 0 {w} {h}" width="100%" height="{h}" '
        f'preserveAspectRatio="xMinYMin meet">{"".join(out)}</svg>'
    )


def labeled_chart(title: str, values: list[float], color: str) -> str:
    """Graphe SVG précédé d'un petit titre."""
    return mark_safe(  # noqa: S308 — voir docstring du module
        f'<div style="margin-top:6px"><div style="font-size:11px;color:#666;'
        f'margin-bottom:4px">{title}</div>{svg_area(values, color)}</div>'
    )
