# Roadmap — Neyla TV

Plateforme de streaming jeux vidéo (type Twitch / Kick). Ce document trace
ce qui est **livré**, ce qui est **en cours**, et la vision **à venir**.
Chaque décision structurante est tracée dans un [ADR](docs/adr/).

Légende : ✅ livré · 🚧 en cours · 📋 planifié · 💡 idée / à challenger

---

## Phases livrées (MVP)

### ✅ Phase 0 — Socle technique
Stack figée, monorepo, Docker Compose, CI GitHub Actions, healthchecks.
→ [ADR 001 — Stack MVP](docs/adr/001-stack-mvp.md)

| Brique | Choix |
|--------|-------|
| Backend | Django 5 + DRF + Channels (ASGS/Daphne) |
| Frontend | Next.js 15 (App Router, Tailwind) |
| Données | PostgreSQL 16 · Redis 7 |
| Async | Celery (worker + beat) |

### ✅ Phase 1 — Comptes & authentification
Inscription, login JWT (access court + refresh cookie HttpOnly), vérification
email, reset mot de passe, profil éditable, rate-limiting des endpoints sensibles.
→ [ADR 002 — Stratégie JWT](docs/adr/002-jwt-strategy.md)

### ✅ Phase 2 — Chaînes & ingest vidéo
Création de chaîne, clé de stream RTMPS, rotation de clé, lecture HLS,
intégration Cloudflare Stream + **mode FAKE** pour développer hors-ligne.
→ [ADR 003 — Cloudflare Stream](docs/adr/003-cloudflare-stream.md)

### ✅ Phase 3 — Statut live
Badge LIVE en quasi temps réel via polling HTTP léger + webhook Cloudflare
signé (HMAC-SHA256, anti-rejeu), compteur de viewers.
→ [ADR 004 — Stratégie live status](docs/adr/004-live-status-strategy.md)

### ✅ Phase 4 — Chat temps réel
Chat WebSocket (Channels + Redis), JWT en query param, historique cappé,
slow-mode, commandes modérateur (`/ban`, `/timeout`, `/unban`, `/slowmode`),
rate-limiting par utilisateur.
→ [ADR 005 — Architecture chat](docs/adr/005-chat-architecture.md)

### ✅ Phase 5 — Découverte & social
Page d'accueil des lives, catégories (jeux), recherche, follow / unfollow,
liste des suivis.
→ [ADR 006 — Découverte & social](docs/adr/006-discovery-and-social.md)

### ✅ Phase 6 — Production (mono-Droplet)
Topologie Droplet + Compose derrière Cloudflare, deploy SSH automatique,
backups Postgres vers Spaces, logs JSON, Sentry serveur.
→ [ADR 007 — Déploiement prod](docs/adr/007-prod-deployment.md)

---

## 🚧 Phase 7 — Déploiement DigitalOcean App Platform (en cours)

Alternative PaaS au Droplet : moins d'ops, scaling déclaratif, bases managées.

- ✅ Spec App Platform versionnée ([`.do/app.yaml`](.do/app.yaml)).
- ✅ Services `api` + `web`, workers `worker` + `beat`, job `migrate` (PRE_DEPLOY).
- ✅ Postgres & Redis managés (TLS), statiques servis par WhiteNoise (sans nginx).
- ✅ Runbook dédié + ADR.
  → [ADR 008 — App Platform](docs/adr/008-app-platform.md) ·
    [Runbook](docs/runbooks/deploy-app-platform.md)
- 🚧 Premier déploiement + domaine custom + secrets Cloudflare réels.

---

## 📋 Prochaines étapes (post-MVP)

### Produit
- 📋 **VOD & rediffusions** : enregistrement des lives, page replay.
- 📋 **Clips** : extraits courts partageables.
- 📋 **Notifications** : "une chaîne suivie passe en live" (web push / email).
- 📋 **Page chaîne enrichie** : panels, réseaux sociaux, planning.
- 💡 **Monétisation** : abonnements, dons, badges abonné dans le chat.

### Plateforme & qualité
- 📋 **Schéma OpenAPI** auto-généré (drf-spectacular) + Swagger UI.
- 📋 **Sentry frontend** (reporté en phase 6, à brancher si bugs non reproductibles).
- 📋 **Tests E2E** (Playwright) sur les parcours critiques.
- 📋 **Observabilité** : métriques (viewers concurrents, latence chat), dashboards.

### Scalabilité (déclencheurs documentés dans l'ADR 007)
- 💡 **MRR > 500 USD** : Postgres HA, scaling horizontal des services.
- 💡 **> 5 000 viewers concurrents** : sharding Redis chat, autoscaling Daphne.
- 💡 **CDN / multi-région** pour le frontend.

---

## Contribuer à la roadmap

Les évolutions structurantes passent par un **ADR** dans
[`docs/adr/`](docs/adr/) (contexte → décision → conséquences). Ouvrez une
issue pour discuter avant d'implémenter une nouvelle phase.
