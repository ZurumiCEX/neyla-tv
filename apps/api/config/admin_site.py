"""Site admin Neyla : page d'accueil enrichie (KPIs + graphiques SVG) + menu groupé.

Le dashboard et la navigation sont best-effort : si une métrique échoue, l'admin
reste accessible.
"""

from __future__ import annotations

import logging

from django.contrib.admin import AdminSite
from django.utils.safestring import mark_safe

from config.admin_icons import ICONS as _ICONS
from config.admin_widgets import svg_area as _svg_area
from config.admin_widgets import svg_donut, svg_hbars

logger = logging.getLogger(__name__)


def _icon(name: str, size: int = 20) -> str:
    body = _ICONS.get(name, _ICONS["dot"])
    return mark_safe(  # noqa: S308 — SVG littéral interne, aucune donnée externe
        f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" '
        f'width="{size}" height="{size}">{body}</svg>'
    )


# Catégories métier du menu latéral : (nom, icône, couleur). Ordre = ordre d'affichage.
_NAV_CATEGORIES: list[tuple[str, str, str]] = [
    ("Audience & comptes", "users", "#FFC81E"),
    ("Création & live", "broadcast", "#3b82f6"),
    ("Monétisation", "cash", "#f59e0b"),
    ("Engagement & gamification", "trophy", "#d946ef"),
    ("Modération & sécurité", "shield", "#f43f5e"),
    ("Système & journaux", "cog", "#8b5cf6"),
]

# Catégorie par défaut selon l'app Django.
_APP_CATEGORY: dict[str, str] = {
    "accounts": "Audience & comptes",
    "social": "Audience & comptes",
    "invitations": "Audience & comptes",
    "channels_app": "Création & live",
    "catalog": "Création & live",
    "streamers": "Création & live",
    "payments": "Monétisation",
    "subscriptions": "Monétisation",
    "gamification": "Engagement & gamification",
    "notifications": "Engagement & gamification",
    "charity": "Engagement & gamification",
    "announcements": "Système & journaux",
    "ops": "Système & journaux",
    "moderation": "Modération & sécurité",
    "safety": "Modération & sécurité",
    "chat": "Modération & sécurité",
    "audit": "Système & journaux",
    "uploads": "Système & journaux",
    "health": "Système & journaux",
    "analytics": "Système & journaux",
}

# Surcharges fines par modèle (object_name en minuscules) — priment sur l'app.
# Ex. : la collaboration (app « social ») relève du live, pas de l'audience.
_MODEL_CATEGORY: dict[str, str] = {
    "collaboration": "Création & live",
    "guide": "Engagement & gamification",
    "guideprogress": "Engagement & gamification",
}

# Choix d'icône par modèle (premier mot-clé trouvé dans le nom, sinon « dot »).
_ITEM_ICON_RULES: list[tuple[str, str]] = [
    ("stream session", "broadcast"),
    ("streamer", "star"),
    ("application", "star"),
    ("stream", "broadcast"),
    ("session", "lock"),
    ("two factor", "lock"),
    ("twofactor", "lock"),
    ("2fa", "lock"),
    ("guide progress", "trophy"),
    ("guide", "book"),
    ("follow", "heart"),
    ("invit", "ticket"),
    ("collaborat", "users"),
    ("channel", "video"),
    ("game", "game"),
    ("wallet", "wallet"),
    ("ledger", "list"),
    ("purchase", "cart"),
    ("tip", "gift"),
    ("payout", "cash"),
    ("fee", "percent"),
    ("sub", "repeat"),
    ("achievement", "trophy"),
    ("banned", "ban"),
    ("ban", "ban"),
    ("report", "flag"),
    ("flag", "flag"),
    ("risk", "alert"),
    ("notification", "bell"),
    ("message", "bell"),
    ("audit", "clipboard"),
    ("event", "clipboard"),
    ("upload", "image"),
    ("media", "image"),
    ("user", "users"),
    ("account", "users"),
]


def _model_icon(name: str) -> str:
    low = name.lower()
    for keyword, icon in _ITEM_ICON_RULES:
        if keyword in low:
            return _icon(icon, 16)
    return _icon("dot", 16)


def _fmt(value) -> str:
    """Sépare les milliers par une espace (lisibilité FR), sinon tel quel."""
    if isinstance(value, int):
        return f"{value:,}".replace(",", " ")
    return str(value)


def _pct(num: float, den: float) -> str:
    return f"{(num / den * 100):.1f} %" if den else "—"


def _ratio(num: float, den: float, unit: str = "") -> str:
    return f"{num / den:,.0f}{unit}".replace(",", " ") if den else "—"


class NeylaAdminSite(AdminSite):
    site_header = "Neyla TV — Administration"
    site_title = "Neyla TV Admin"
    index_title = "Tableau de bord plateforme"
    index_template = "admin/neyla_index.html"

    # ---- Navigation latérale groupée -------------------------------------
    def each_context(self, request):
        ctx = super().each_context(request)
        try:
            ctx["nav_groups"] = self._build_nav(request)
        except Exception:  # noqa: BLE001 — la navigation ne doit jamais casser l'admin
            logger.exception("admin nav build failed")
            ctx["nav_groups"] = []
        return ctx

    def _build_nav(self, request) -> list[dict]:
        """Menu groupé par catégorie métier, depuis ``get_app_list``.

        Les liens sont filtrés par permissions (donc toujours valides) ; chaque
        entrée reçoit une icône déduite de son nom. Le placement suit l'app, avec
        surcharges fines par modèle (``_MODEL_CATEGORY``).
        """
        path = request.path
        buckets: dict[str, list] = {name: [] for name, _, _ in _NAV_CATEGORIES}
        buckets["Autres"] = []

        for app in self.get_app_list(request):
            for model in app.get("models", []):
                url = model.get("admin_url")
                if not url:
                    continue
                obj = (model.get("object_name") or "").lower()
                category = _MODEL_CATEGORY.get(obj) or _APP_CATEGORY.get(app["app_label"], "Autres")
                buckets.setdefault(category, []).append(
                    {
                        "label": model["name"],
                        "url": url,
                        "active": path.startswith(url),
                        "icon": _model_icon(model["name"]),
                    }
                )

        meta = {name: (icon, color) for name, icon, color in _NAV_CATEGORIES}
        meta["Autres"] = ("cog", "#64748b")
        groups = []
        for name in [*[c[0] for c in _NAV_CATEGORIES], "Autres"]:
            items = buckets.get(name) or []
            if not items:
                continue
            icon, color = meta[name]
            groups.append(
                {
                    "name": name,
                    "icon": _icon(icon),
                    "color": color,
                    "items": sorted(items, key=lambda i: i["label"]),
                    "open": any(i["active"] for i in items),
                }
            )
        if groups and not any(g["open"] for g in groups):
            groups[0]["open"] = True
        return groups

    # ---- Tableau de bord -------------------------------------------------
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
        com = m.get("commerce", {})
        cnt = m.get("content", {})
        liv = m.get("live", {})
        totals = rev["totals"]
        series = rev["series"]
        new_users = [p["count"] for p in m["new_users_series"]]
        purchases = [p["purchases_xof"] for p in series]
        commission = [p["platform_commission_aura"] for p in series]
        tips = [p["tips_aura"] for p in series]
        creator_share = max(0, totals["tips_aura"] - totals["platform_commission_aura"])
        purchasers = com.get("paying_users", 0)

        hero = [
            self._hero(
                "Utilisateurs",
                ov["users_total"],
                f"+{gr['new_users_7d']} cette semaine",
                "users",
                new_users,
                "#FFC81E",
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

        ratios = [
            {
                "label": "ARPU 30j",
                "value": _ratio(totals["purchases_xof"], ov["users_total"], " F"),
                "hint": "Revenu moyen / utilisateur",
            },
            {
                "label": "Conversion acheteurs",
                "value": _pct(purchasers, ov["users_total"]),
                "hint": "Utilisateurs ayant payé",
            },
            {
                "label": "Engagement (DAU/MAU)",
                "value": _pct(ov["dau"], ov["mau"]),
                "hint": "Stickiness",
            },
            {
                "label": "Taux en direct",
                "value": _pct(ov["live_now"], ov["streamers_total"]),
                "hint": "Streamers live maintenant",
            },
            {
                "label": "Heures / stream",
                "value": _ratio(ov["broadcast_hours"], ov["streams_total"], " h"),
                "hint": "Durée moyenne de session",
            },
            {
                "label": "Abonnés / chaîne",
                "value": _ratio(cnt.get("follows_total", 0), ov["streamers_total"]),
                "hint": "Followers moyens",
            },
            {
                "label": "Tip moyen",
                "value": _ratio(totals["tips_aura"], com.get("tips_count", 0), " Aura"),
                "hint": "Aura par tip",
            },
            {
                "label": "Commission / tips",
                "value": _pct(totals["platform_commission_aura"], totals["tips_aura"]),
                "hint": "Part plateforme",
            },
            {
                "label": "Part créateurs",
                "value": _pct(creator_share, totals["tips_aura"]),
                "hint": "Tips reversés aux créateurs",
            },
            {
                "label": "Taux d'abonnement",
                "value": _pct(cnt.get("subscriptions_active", 0), cnt.get("follows_total", 0)),
                "hint": "Abonnés payants / followers",
            },
            {
                "label": "Streamers / users",
                "value": _pct(ov["streamers_total"], ov["users_total"]),
                "hint": "Part de créateurs",
            },
            {
                "label": "Récompenses / user",
                "value": _ratio(cnt.get("achievements_unlocked", 0), ov["users_total"]),
                "hint": "Succès débloqués",
            },
        ]

        charts = [
            self._chart("Inscriptions / jour", new_users, "#FFC81E"),
            self._chart("Revenus achats / jour (FCFA)", purchases, "#3b82f6"),
            self._chart("Commission / jour (Aura)", commission, "#f59e0b"),
            self._chart("Tips / jour (Aura)", tips, "#d946ef"),
        ]

        breakdown = [
            ("Tips créateurs", creator_share, "#d946ef"),
            ("Abonnements", totals["subs_aura"], "#FFC81E"),
            ("Commission", totals["platform_commission_aura"], "#f59e0b"),
        ]
        donut = {
            "title": "Économie Aura — 30j",
            "svg": svg_donut(breakdown),
            "legend": [
                {"label": label, "value": _fmt(val), "color": color}
                for label, val, color in breakdown
            ],
        }
        top = ov.get("top_streamers", [])[:6]
        streamers_bars = {
            "title": "Top streamers (abonnés)",
            "svg": svg_hbars([(s["username"], s["followers"]) for s in top], "#3b82f6"),
            "empty": not top,
        }
        games = liv.get("top_games", [])
        games_bars = {
            "title": "Top jeux (chaînes)",
            "svg": svg_hbars([(g["name"], g["channels"]) for g in games], "#8b5cf6"),
            "empty": not games,
        }
        live_now = {"channels": liv.get("channels", []), "empty": not liv.get("channels")}

        sections = [
            {
                "name": "Audience",
                "icon": _icon("users"),
                "items": [
                    {"label": "Actifs 24h (DAU)", "value": _fmt(ov["dau"])},
                    {"label": "Actifs 30j (MAU)", "value": _fmt(ov["mau"])},
                    {"label": "Inscrits 7j", "value": _fmt(gr["new_users_7d"])},
                    {"label": "Followers cumulés", "value": _fmt(cnt.get("follows_total", 0))},
                ],
            },
            {
                "name": "Création & live",
                "icon": _icon("broadcast"),
                "items": [
                    {"label": "Streamers", "value": _fmt(ov["streamers_total"])},
                    {"label": "En direct", "value": _fmt(ov["live_now"])},
                    {"label": "Streams 7j", "value": _fmt(ov["streams_7d"])},
                    {"label": "Heures diffusées", "value": _fmt(ov["broadcast_hours"])},
                    {"label": "Pic simultané", "value": _fmt(ov["peak_concurrent"])},
                    {"label": "Jeux / catégories", "value": _fmt(cnt.get("games_count", 0))},
                    {"label": "Candidatures en attente", "value": _fmt(cnt.get("apps_pending", 0))},
                ],
            },
            {
                "name": "Monétisation",
                "icon": _icon("cash"),
                "items": [
                    {"label": "Revenus 30j (FCFA)", "value": _fmt(totals["purchases_xof"])},
                    {"label": "Acheteurs 30j", "value": _fmt(purchasers)},
                    {"label": "Tips 30j (Aura)", "value": _fmt(totals["tips_aura"])},
                    {"label": "Part créateurs (Aura)", "value": _fmt(creator_share)},
                    {"label": "Abos actifs", "value": _fmt(cnt.get("subscriptions_active", 0))},
                    {"label": "Abos 30j (Aura)", "value": _fmt(totals["subs_aura"])},
                ],
            },
            {
                "name": "Modération",
                "icon": _icon("shield"),
                "items": [
                    {"label": "Signalements ouverts", "value": _fmt(mod["open_reports"])},
                    {"label": "Contenus à examiner", "value": _fmt(mod["pending_flags"])},
                    {"label": "Bloqués auto.", "value": _fmt(mod["auto_blocked"])},
                    {"label": "Risques ouverts", "value": _fmt(mod["open_risk"])},
                    {"label": "Retraits en attente", "value": _fmt(mod["pending_payouts"])},
                ],
            },
        ]
        return {
            "hero": hero,
            "ratios": ratios,
            "charts": charts,
            "donut": donut,
            "streamers_bars": streamers_bars,
            "games_bars": games_bars,
            "live_now": live_now,
            "sections": sections,
        }

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
