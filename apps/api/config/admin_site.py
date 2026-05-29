"""Site admin Neyla : page d'accueil enrichie (KPIs + graphiques SVG).

Le dashboard est best-effort : si une métrique échoue, l'admin reste accessible.
"""

from __future__ import annotations

import logging

from django.contrib.admin import AdminSite
from django.utils.safestring import mark_safe

from config.admin_widgets import svg_area as _svg_area

logger = logging.getLogger(__name__)


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
