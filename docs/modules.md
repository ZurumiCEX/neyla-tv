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
  `display_name`, `avatar_url`, `bio`, `email_verified_at`). `AUTH_USER_MODEL`.
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
| `/c/[slug]` | `page.tsx` | Page chaîne : player + chat |
| `/categories/[slug]` | `page.tsx` | Lives d'une catégorie |
| `/search` | `SearchView.tsx` | Recherche |

### Composants — `src/components/`
`HlsPlayer` (lecture HLS via hls.js), `ChatPanel` (WebSocket chat),
`LiveBadge`, `LiveCard`, `FollowButton`, `Navbar`.

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
