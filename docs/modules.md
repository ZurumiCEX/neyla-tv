# Modules — Neyla TV

Vue d'ensemble des modules du monorepo : responsabilités, modèles de données
et points d'entrée. Pour le détail des endpoints, voir [`api.md`](api.md).

```
apps/
├── api/   # Django 5 — REST + WebSocket + tâches async
└── web/   # Next.js 15 — App Router, SSR + composants client
infra/     # Dockerfiles, compose, nginx, scripts
docs/      # ADR + runbooks + cette doc
.do/       # Spec DigitalOcean App Platform
```

---

## Backend — `apps/api/` (Django)

Projet Django `config` (settings `base`/`dev`/`prod`, ASGI via Daphne, Celery).
Chaque app est autonome : `models`, `views`, `serializers`, `services`,
`urls`, `tests`, `factories`.

### `accounts` — identité & authentification
- **Rôle** : utilisateurs, JWT (access + refresh cookie), vérification email,
  reset mot de passe, profil.
- **Modèle** : `User` (email unique, username `^[a-z0-9_]{3,30}$`,
  `display_name`, `avatar_url`, `bio`, `email_verified_at`, `terms_accepted_at`,
  `invited_by`). `AUTH_USER_MODEL`. L'inscription **exige** `terms_accepted=true`
  (attestation 13 ans + CGU).
- **À noter** : `tokens.py` (génération de tokens email signés), `tasks.py`
  (envoi email via Celery), `services.py` (logique métier). Hash Argon2.
- → [ADR 002](adr/002-jwt-strategy.md)

### `channels_app` — chaînes & ingest vidéo
- **Rôle** : chaîne d'un streamer, clé RTMPS, lecture HLS, intégration
  Cloudflare Stream, webhook de statut live.
- **Modèle** : `Channel` (OneToOne `User`, `slug`, `title`, `category` FK→`Game`,
  `live_input_uid`, `rtmps_url`, `rtmps_key`, `hls_playback_url`, `is_live`).
- **À noter** : `cloudflare.py` (client réel + **client FAKE** si pas de token),
  `webhooks.py` (vérif HMAC), `signals.py`, `tasks.py`.
- → [ADR 003](adr/003-cloudflare-stream.md) · [ADR 004](adr/004-live-status-strategy.md)

### `chat` — chat temps réel
- **Rôle** : WebSocket chat (Channels), historique, slow-mode, modération.
- **Modèle** : `ChatBan` (`channel`, `user`, `until` null=permanent, `reason`).
  Les **messages** ne sont pas en base : ils vivent dans Redis (éphémères).
- **À noter** : `consumers.py` (ChatConsumer), `routing.py` (route WS),
  `middleware.py` (auth JWT en query param), `redis_store.py` (messages,
  viewers, rate-limit, slow-mode).
- → [ADR 005](adr/005-chat-architecture.md)

### `catalog` — découverte & jeux
- **Rôle** : page des lives, catégories (jeux), recherche.
- **Modèle** : `Game` (`slug`, `name`, `box_art_url`). Seed :
  `catalog/fixtures/games_seed.json`.
- → [ADR 006](adr/006-discovery-and-social.md)

### `social` — graphe de follow
- **Rôle** : suivre / ne plus suivre, liste des suivis, statut.
- **Modèle** : `Follow` (`follower`, `followee`, unique ensemble).
- → [ADR 006](adr/006-discovery-and-social.md)

### `health` — sondes
- **Rôle** : `/api/healthz` → ping Postgres + Redis (`200`/`503`). Sans modèle.
  Utilisé par les health checks de la plateforme.

### Modules v2 (enterprise)

- **`accounts` (étendu)** : `User.role` (`user/support/moderator/admin`) +
  `permissions.py` (`IsAdminRole`/`IsModerator`/`IsSupport`), `invited_by`
  (parrainage), `admin_views.py` (gestion utilisateurs).
- **`payments` (étendu)** : devise **XOF** + `conversion.py` (EUR fixe / USD
  manuel) ; `FeeRule` + `split(montant, produit)` (remplace `CREATOR_SHARE`) ;
  ledger enrichi (`currency`/`related_*`/`metadata`) ; `admin_views.py`
  (transactions unifiées, commissions, résolution payouts).
- **`audit`** : `AuditEvent` (`actor`, `action`, `target`, `meta`) + `record()`,
  appelé sur les actions sensibles (approbation, payout, changement de rôle…).
- **`uploads`** : `services.upload_image()` vers **Cloudflare R2** (boto3, mode
  FAKE hors-ligne) ; endpoints avatar / bannière / vignette de jeu.
- **`subscriptions`** : `SubTier` (palier prix Aura + perks) et `Subscription`
  (statut, période, `gifted_by` pour les cadeaux) ; `subscribe()` débite le wallet
  via `split`, `gift_subscription()` permet d'offrir un abonnement à un autre
  utilisateur. Endpoints : `POST /subscriptions/gift`, `GET /subscriptions/gifted`.
- **`gamification`** : `Achievement` / `UserAchievement` ;
  `check_and_award(user, event)` (best-effort) hooké dans login, candidature,
  live, follow, tip, abonnement.
- **`invitations`** : `Invite` (code, max_uses, expiry) ; redemption à
  l'inscription (`?invite=CODE`) → `User.invited_by`. **La récompense de
  parrainage (Aura) est versée à la *vérification de l'email* du filleul**
  (anti-abus) ; `successful_count()` ne compte que les filleuls vérifiés.
- **`notifications` (étendu)** : nouveaux types, `NotificationPreference` par
  type, messagerie support (`POST /api/admin/messages`).
- **`moderation` (étendu)** : import de mots interdits, workflow de signalements
  (`assigned_to`/`resolution`/`resolved_at`, ban depuis le report).
- **`analytics` (étendu)** : `admin_dashboard()` (activité + séries de revenus
  plateforme), `creator_revenue(user, period)` (revenus consolidés d'un
  créateur — tips + abonnements + parrainage — par jour/semaine/mois).

### `config` — projet Django
- `settings/base.py` (commun), `dev.py` (DEBUG, hosts permissifs),
  `prod.py` (sécurité, WhiteNoise, logs JSON, Sentry).
- `asgi.py` (HTTP Django + WebSocket Channels), `wsgi.py`, `celery.py`,
  `urls.py` (montage des apps).

---

## Frontend — `apps/web/` (Next.js 15, App Router)

### Pages — `src/app/`
| Route | Fichier | Rôle |
|-------|---------|------|
| `/` | `page.tsx` | Accueil : lives + santé des services |
| `/login`, `/register` | `*/page.tsx` | Auth |
| `/verify-email/[token]` | `page.tsx` | Vérification email |
| `/dashboard` | `page.tsx` | Espace streamer (clé RTMPS, chaîne) |
| `/revenus` | `page.tsx` | Revenus consolidés du créateur (tips + abos + parrainage), période jour/semaine/mois |
| `/abonnements` | `page.tsx` | Mes abonnements + cadeau d'abonnement (onglets Actifs/Offert) |
| `/c/[slug]` | `page.tsx` | Page chaîne : player + chat + **bouton partager** |
| `/categories/[slug]` | `page.tsx` | Lives d'une catégorie |
| `/search` | `SearchView.tsx` | Recherche |

### Composants — `src/components/`
`HlsPlayer` (lecture HLS via hls.js), `ChatPanel` (WebSocket chat),
`LiveBadge`, `LiveCard`, `FollowButton`, `Navbar`, `ProfileMenu`
(menu utilisateur incl. **Revenus** [streamers] et **Abonnements**),
`ShareButton` (partage live : copie de lien interne + X/Facebook/WhatsApp/
Telegram + Web Share API natif), `Footer` (4 colonnes incl. Légal + gros logo).

### Librairie — `src/lib/`
- `api.ts` : `apiFetch` (client, `NEXT_PUBLIC_API_URL`) et `apiFetchServer`
  (SSR, `API_URL_INTERNAL`).
- `auth-context.tsx` : contexte React (access token en mémoire, refresh
  via cookie).

---

## Infrastructure — `infra/`

| Chemin | Rôle |
|--------|------|
| `docker/api.Dockerfile` | Image API multi-stage (`dev` / `prod`, collectstatic au build) |
| `docker/web.Dockerfile` | Image Next.js multi-stage (build standalone) |
| `docker/nginx.Dockerfile` | Reverse-proxy prod (topologie Droplet) |
| `docker/backup.Dockerfile` + `backup.crontab` | Dump Postgres → Spaces |
| `compose/docker-compose.yml` | Dev (tous les services) |
| `compose/docker-compose.prod.yml` | Prod Droplet |
| `scripts/backup-postgres.sh` | Script de dump |

> Sur **DigitalOcean App Platform**, nginx et le backup Compose ne sont pas
> utilisés : les bases sont managées et l'ingress est géré par la plateforme.
> Voir [`.do/app.yaml`](../.do/app.yaml) et
> [le runbook](runbooks/deploy-app-platform.md).

---

## Flux de données (résumé)

```
Navigateur ──HTTP──▶ web (Next.js)         page SSR + assets
          ──HTTP──▶ api (DRF)              REST /api/*
          ──WSS───▶ api (Channels)         chat /ws/*
OBS ──RTMPS──▶ Cloudflare Stream ──HLS──▶ Navigateur (HlsPlayer)
Cloudflare ──webhook signé──▶ api          bascule is_live
api ◀──▶ Postgres (durable) · Redis (chat éphémère, channel layer, Celery)
Celery worker/beat ◀──▶ Redis              emails, tâches async
```
