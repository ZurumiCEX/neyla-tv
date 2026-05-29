"""Site admin Neyla : page d'accueil enrichie (KPIs + graphiques SVG).

Le dashboard est best-effort : si une métrique échoue, l'admin reste accessible.
"""

from __future__ import annotations

import logging

from django.contrib.admin import AdminSite
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


def _svg_area(values: list[float], color: str, w: int = 280, h: int = 60) -> str:
    """Mini graphe (aire + ligne) en SVG inline, sans dépendance."""
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
        f'style="width:100%;height:{h}px">'
        f'<path d="{area}" fill="{color}" opacity="0.18"/>'
        f'<path d="{line}" fill="none" stroke="{color}" stroke-width="2" '
        f'vector-effect="non-scaling-stroke"/></svg>'
    )


class NeylaAdminSite(AdminSite):
    site_header = "Neyla TV — Administration"
    site_title = "Neyla TV Admin"
    index_title = "Tableau de bord plateforme"
    index_template = "admin/neyla_index.html"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        try:
            extra_context["dashboard"] = self._build_dashboard()
        except Exception:  # noqa: BLE001 — l'admin doit rester accessible
            logger.exception("admin dashboard metrics failed")
            extra_context["dashboard"] = None
        return super().index(request, extra_context)

    def _build_dashboard(self) -> dict:
        from analytics.services import admin_dashboard_metrics

        m = admin_dashboard_metrics(30)
        ov, gr, rev, mod = m["overview"], m["growth"], m["revenue"], m["moderation"]
        series = rev["series"]
        totals = rev["totals"]
        new_users = [p["count"] for p in m["new_users_series"]]
        purchases = [p["purchases_xof"] for p in series]
        commission = [p["platform_commission_aura"] for p in series]
        tips = [p["tips_aura"] for p in series]

        kpis = [
            {"label": "Utilisateurs", "value": ov["users_total"], "group": "Audience"},
            {"label": "Actifs 24h (DAU)", "value": ov["dau"], "group": "Audience"},
            {"label": "Actifs 30j (MAU)", "value": ov["mau"], "group": "Audience"},
            {"label": "Inscrits 7j", "value": gr["new_users_7d"], "group": "Audience"},
            {"label": "Streamers", "value": ov["streamers_total"], "group": "Contenu"},
            {"label": "En direct", "value": ov["live_now"], "group": "Contenu"},
            {"label": "Streams 7j", "value": ov["streams_7d"], "group": "Contenu"},
            {"label": "Heures diffusées", "value": ov["broadcast_hours"], "group": "Contenu"},
            {"label": "Revenus 30j (FCFA)", "value": totals["purchases_xof"], "group": "Revenus"},
            {"label": "Tips 30j (Aura)", "value": totals["tips_aura"], "group": "Revenus"},
            {"label": "Abos 30j (Aura)", "value": totals["subs_aura"], "group": "Revenus"},
            {
                "label": "Commission 30j (Aura)",
                "value": totals["platform_commission_aura"],
                "group": "Revenus",
            },
            {"label": "Signalements ouverts", "value": mod["open_reports"], "group": "Modération"},
            {"label": "Contenus à examiner", "value": mod["pending_flags"], "group": "Modération"},
            {"label": "Risques ouverts", "value": mod["open_risk"], "group": "Modération"},
            {
                "label": "Retraits en attente",
                "value": mod["pending_payouts"],
                "group": "Modération",
            },
        ]
        charts = [
            self._chart("Inscriptions / jour (30j)", new_users, "#10b981"),
            self._chart("Revenus achats / jour (FCFA)", purchases, "#3b82f6"),
            self._chart("Commission / jour (Aura)", commission, "#f59e0b"),
            self._chart("Tips / jour (Aura)", tips, "#d946ef"),
        ]
        return {"kpis": kpis, "charts": charts}

    @staticmethod
    def _chart(title: str, values: list, color: str) -> dict:
        # SVG construit uniquement à partir de valeurs numériques + couleurs
        # littérales internes ; aucune donnée utilisateur n'y est interpolée.
        return {"title": title, "svg": mark_safe(_svg_area(values, color))}  # noqa: S308
