"""Site admin Neyla : page d'accueil enrichie (KPIs + graphiques SVG).

Le dashboard est best-effort : si une métrique échoue, l'admin reste accessible.
"""

from __future__ import annotations

import logging

from django.contrib.admin import AdminSite
from django.utils.safestring import mark_safe

from config.admin_widgets import svg_area as _svg_area

logger = logging.getLogger(__name__)

# Icônes inline (style Heroicons outline, héritent de currentColor).
_ICONS = {
    "users": (
        '<path d="M17 20h5v-2a4 4 0 0 0-3-3.87M9 20H4v-2a4 4 0 0 1 3-3.87'
        'm6-1.13a4 4 0 1 0-4 0M17 7a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/>'
    ),
    "cash": (
        '<rect x="2" y="6" width="20" height="12" rx="2"/>'
        '<circle cx="12" cy="12" r="2.5"/><path d="M6 12h.01M18 12h.01"/>'
    ),
    "live": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M5.5 5.5a9 9 0 0 0 0 13M18.5 5.5a9 9 0 0 1 0 13"/>'
    ),
    "shield": '<path d="M12 3 4 6v6c0 5 3.5 7.5 8 9 4.5-1.5 8-4 8-9V6l-8-3Z"/>',
    "play": '<path d="M5 4v16M19 4v16M5 9h14M5 15h14"/>',
    "gift": (
        '<rect x="3" y="8" width="18" height="13" rx="1"/>'
        '<path d="M3 12h18M12 8v13M12 8S9 3 7 5s5 3 5 3 3-5 5-3-5 3-5 3"/>'
    ),
    "grid": (
        '<rect x="3" y="3" width="7" height="7" rx="1"/>'
        '<rect x="14" y="3" width="7" height="7" rx="1"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1"/>'
        '<rect x="14" y="14" width="7" height="7" rx="1"/>'
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
}

# Regroupement des modules d'administration en catégories métier (ordre + icône).
# Les apps non listées tombent dans « Autres ».
_NAV_CATEGORIES: list[tuple[str, str, set[str]]] = [
    ("Comptes & audience", "users", {"accounts", "social", "invitations"}),
    ("Contenu & live", "play", {"channels_app", "catalog", "streamers"}),
    ("Monétisation", "cash", {"payments", "subscriptions", "gamification"}),
    ("Modération & sécurité", "shield", {"moderation", "safety", "chat"}),
    ("Système & journaux", "cog", {"analytics", "notifications", "audit", "uploads", "health"}),
]


def _icon(name: str) -> str:
    body = _ICONS.get(name, "")
    return mark_safe(  # noqa: S308 — SVG littéral interne, aucune donnée externe
        f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
        f'width="20" height="20">{body}</svg>'
    )


def _fmt(value) -> str:
    """Sépare les milliers par une espace fine (lisibilité FR), sinon tel quel."""
    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")
    return str(value)


class NeylaAdminSite(AdminSite):
    site_header = "Neyla TV — Administration"
    site_title = "Neyla TV Admin"
    index_title = "Tableau de bord plateforme"
    index_template = "admin/neyla_index.html"

    def each_context(self, request):
        ctx = super().each_context(request)
        try:
            ctx["nav_groups"] = self._build_nav(request)
        except Exception:  # noqa: BLE001 — la navigation ne doit jamais casser l'admin
            logger.exception("admin nav build failed")
            ctx["nav_groups"] = []
        return ctx

    def _build_nav(self, request) -> list[dict]:
        """Construit le menu latéral groupé par catégorie métier.

        S'appuie sur ``get_app_list`` (modèles réellement enregistrés + permissions
        de l'utilisateur), donc les liens sont toujours valides et filtrés par droit.
        """
        by_label: dict[str, list] = {}
        for app in self.get_app_list(request):
            by_label.setdefault(app["app_label"], []).extend(app.get("models", []))

        path = request.path

        def _item(model: dict) -> dict | None:
            url = model.get("admin_url")
            if not url:
                return None
            return {"label": model["name"], "url": url, "active": path.startswith(url)}

        groups: list[dict] = []
        used: set[str] = set()
        for name, icon, labels in _NAV_CATEGORIES:
            items = []
            for label in labels:
                used.add(label)
                items += [it for m in by_label.get(label, []) if (it := _item(m))]
            if items:
                groups.append(
                    {
                        "name": name,
                        "icon": _icon(icon),
                        "items": sorted(items, key=lambda i: i["label"]),
                    }
                )

        leftovers = []
        for label, models in by_label.items():
            if label in used:
                continue
            leftovers += [it for m in models if (it := _item(m))]
        if leftovers:
            groups.append(
                {
                    "name": "Autres",
                    "icon": _icon("cog"),
                    "items": sorted(leftovers, key=lambda i: i["label"]),
                }
            )
        return groups

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

        hero = [
            self._hero(
                "Utilisateurs",
                ov["users_total"],
                f"+{gr['new_users_7d']} cette semaine",
                "users",
                new_users,
                "#10b981",
            ),
            self._hero(
                "Revenus 30j (FCFA)",
                totals["purchases_xof"],
                "Achats crédités",
                "cash",
                purchases,
                "#3b82f6",
            ),
            self._hero(
                "Commission 30j",
                totals["platform_commission_aura"],
                "Aura plateforme",
                "shield",
                commission,
                "#f59e0b",
            ),
            self._hero(
                "Tips 30j",
                totals["tips_aura"],
                "Aura offerts aux créateurs",
                "gift",
                tips,
                "#d946ef",
            ),
        ]
        charts = [
            self._chart("Inscriptions / jour", new_users, "#10b981"),
            self._chart("Revenus achats / jour (FCFA)", purchases, "#3b82f6"),
            self._chart("Commission / jour (Aura)", commission, "#f59e0b"),
            self._chart("Tips / jour (Aura)", tips, "#d946ef"),
        ]
        sections = [
            {
                "name": "Audience",
                "icon": _icon("users"),
                "items": [
                    {"label": "Actifs 24h (DAU)", "value": _fmt(ov["dau"])},
                    {"label": "Actifs 30j (MAU)", "value": _fmt(ov["mau"])},
                    {"label": "Inscrits 7j", "value": _fmt(gr["new_users_7d"])},
                ],
            },
            {
                "name": "Contenu",
                "icon": _icon("play"),
                "items": [
                    {"label": "Streamers", "value": _fmt(ov["streamers_total"])},
                    {"label": "En direct", "value": _fmt(ov["live_now"])},
                    {"label": "Streams 7j", "value": _fmt(ov["streams_7d"])},
                    {"label": "Heures diffusées", "value": _fmt(ov["broadcast_hours"])},
                ],
            },
            {
                "name": "Revenus",
                "icon": _icon("cash"),
                "items": [
                    {"label": "Abos 30j (Aura)", "value": _fmt(totals["subs_aura"])},
                    {"label": "Tips 30j (Aura)", "value": _fmt(totals["tips_aura"])},
                ],
            },
            {
                "name": "Modération",
                "icon": _icon("shield"),
                "items": [
                    {"label": "Signalements ouverts", "value": _fmt(mod["open_reports"])},
                    {"label": "Contenus à examiner", "value": _fmt(mod["pending_flags"])},
                    {"label": "Risques ouverts", "value": _fmt(mod["open_risk"])},
                    {"label": "Retraits en attente", "value": _fmt(mod["pending_payouts"])},
                ],
            },
        ]
        return {"hero": hero, "charts": charts, "sections": sections}

    @staticmethod
    def _hero(label, value, sub, icon, values, color) -> dict:
        return {
            "label": label,
            "value": _fmt(value),
            "sub": sub,
            "icon": _icon(icon),
            "color": color,
            "svg": mark_safe(_svg_area(values, color, w=300, h=40)),  # noqa: S308
        }

    @staticmethod
    def _chart(title: str, values: list, color: str) -> dict:
        # SVG construit uniquement à partir de valeurs numériques + couleurs
        # littérales internes ; aucune donnée utilisateur n'y est interpolée.
        return {"title": title, "svg": mark_safe(_svg_area(values, color))}  # noqa: S308
