<div align="center">

# 🎮 Neyla TV

**Plateforme de streaming jeux vidéo — type Twitch / Kick.**

REST + WebSocket, ingest RTMPS → HLS, chat temps réel, découverte & social.

[![CI](https://github.com/ZurumiCEX/neyla-tv/actions/workflows/ci.yml/badge.svg)](https://github.com/ZurumiCEX/neyla-tv/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Roadmap](https://img.shields.io/badge/roadmap-MVP%20%E2%9C%93-success)](ROADMAP.md)
[![ADR](https://img.shields.io/badge/decisions-8%20ADR-informational)](docs/adr/)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.1-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.15-A30000?logo=django&logoColor=white)
![Channels](https://img.shields.io/badge/Channels-WebSocket-092E20?logo=django&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-000000?logo=next.js&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![Tailwind](https://img.shields.io/badge/Tailwind-3-06B6D4?logo=tailwindcss&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5-37814A?logo=celery&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![DigitalOcean](https://img.shields.io/badge/DigitalOcean-App%20Platform-0080FF?logo=digitalocean&logoColor=white)

[Roadmap](ROADMAP.md) · [API](docs/api.md) · [Modules](docs/modules.md) · [ADR](docs/adr/) · [Déploiement](docs/runbooks/deploy-app-platform.md)

</div>

---

## ✨ Fonctionnalités

- 🔐 **Comptes & JWT** — inscription, login (access court + refresh cookie HttpOnly), vérif email, reset mot de passe.
- 📡 **Ingest vidéo** — clé RTMPS par chaîne, lecture HLS, Cloudflare Stream (+ **mode FAKE** hors-ligne).
- 🔴 **Statut live** — badge LIVE quasi temps réel + webhook Cloudflare signé (HMAC, anti-rejeu).
- 💬 **Chat temps réel** — WebSocket (Channels + Redis), slow-mode, modération (`/ban`, `/timeout`, `/slowmode`).
- 🔎 **Découverte & social** — lives, catégories, recherche, follow / unfollow.
- ⚙️ **Async** — Celery worker + beat (emails, tâches planifiées).

## 🏗️ Architecture

```
                 ┌──────────── DigitalOcean App Platform (ou Droplet) ───────────┐
Navigateur ─HTTP─▶│  web (Next.js 15)   ──/──                                     │
           ─HTTP─▶│  api (Django/DRF)   ──/api──        ┌── Postgres 16 (durable) │
           ─WSS──▶│  api (Channels)     ──/ws──   ◀────▶│── Redis 7 (chat, layer, │
                  │  worker · beat (Celery)             │              Celery)    │
                  └──────────────────────────────────────────────────────────────┘
OBS ─RTMPS─▶ Cloudflare Stream ─HLS─▶ Navigateur     Cloudflare ─webhook signé─▶ api
```

Stack figée dans [`docs/adr/001-stack-mvp.md`](docs/adr/001-stack-mvp.md).
Détail des modules : [`docs/modules.md`](docs/modules.md).

## 🚀 Démarrage rapide (local)

**Prérequis** : Docker + Docker Compose v2, `make`, Git.

```bash
cp .env.example .env
make up          # build + démarre tous les services
make migrate     # applique les migrations Django
make logs        # suivi des logs
```

| Service   | URL                                |
|-----------|------------------------------------|
| Frontend  | http://localhost:3000              |
| API       | http://localhost:8000/api/healthz  |
| Admin     | http://localhost:8000/admin/       |
| Postgres  | localhost:5432                     |
| Redis     | localhost:6379                     |

La page d'accueil affiche l'état de l'API, Postgres et Redis (pastilles vertes attendues).

**Premières étapes après bootstrap**

```bash
docker compose -f infra/compose/docker-compose.yml exec api \
  python manage.py loaddata catalog/fixtures/games_seed.json   # seed des jeux
docker compose -f infra/compose/docker-compose.yml exec api \
  python manage.py createsuperuser                             # admin
```

## 🧰 Commandes utiles

| Commande        | Effet                                          |
|-----------------|------------------------------------------------|
| `make up`       | Build + démarre tous les services              |
| `make down`     | Stoppe et supprime les conteneurs              |
| `make logs`     | Logs en suivi                                  |
| `make migrate`  | Applique les migrations Django                 |
| `make shell`    | Shell Django dans le conteneur API             |
| `make test`     | pytest (API) + tests web                       |
| `make lint`     | Ruff + Black --check + ESLint                  |
| `make format`   | Auto-fix (Ruff, Black, isort, Prettier)        |

## 📁 Structure

```
apps/
  api/     # Django 5 — accounts · channels_app · chat · catalog · social · health
  web/     # Next.js 15 — App Router, Tailwind
infra/
  docker/  # Dockerfiles api · web · nginx · backup (multi-stage dev/prod)
  compose/ # docker-compose.yml (dev) + .prod.yml (Droplet)
  nginx/   # config nginx prod
docs/
  adr/       # Architecture Decision Records (001 → 008)
  runbooks/  # deploy · deploy-app-platform · restore-postgres · incident-response
  api.md · modules.md
.do/
  app.yaml   # spec DigitalOcean App Platform
```

## ☁️ Déploiement

### Option A — DigitalOcean App Platform (PaaS, recommandé)

Toute la prod tient dans [`.do/app.yaml`](.do/app.yaml) : services `api`+`web`,
workers Celery, job de migration, Postgres & Redis managés.

```bash
doctl apps create --spec .do/app.yaml
```

Guide complet : [`docs/runbooks/deploy-app-platform.md`](docs/runbooks/deploy-app-platform.md)
· compromis : [`docs/adr/008-app-platform.md`](docs/adr/008-app-platform.md).

### Option B — Droplet + Docker Compose

Un Droplet derrière Cloudflare (TLS + WAF), deploy SSH automatique, backups
Postgres → Spaces. Détails : [`docs/adr/007-prod-deployment.md`](docs/adr/007-prod-deployment.md)
· runbook : [`docs/runbooks/deploy.md`](docs/runbooks/deploy.md).

## 📚 Documentation

| Doc | Contenu |
|-----|---------|
| [ROADMAP.md](ROADMAP.md) | Phases livrées + vision à venir |
| [docs/api.md](docs/api.md) | Référence API (REST + WebSocket + webhooks) |
| [docs/modules.md](docs/modules.md) | Modules backend/frontend & modèles |
| [docs/adr/](docs/adr/) | Décisions d'architecture (001 → 008) |
| [docs/runbooks/](docs/runbooks/) | Deploy, restore Postgres, incident response |

<details>
<summary><b>Index des ADR</b></summary>

1. [Stack MVP](docs/adr/001-stack-mvp.md)
2. [Stratégie JWT](docs/adr/002-jwt-strategy.md)
3. [Cloudflare Stream (+ mode FAKE)](docs/adr/003-cloudflare-stream.md)
4. [Statut live (poll HTTP)](docs/adr/004-live-status-strategy.md)
5. [Architecture chat](docs/adr/005-chat-architecture.md)
6. [Découverte & social](docs/adr/006-discovery-and-social.md)
7. [Déploiement Droplet](docs/adr/007-prod-deployment.md)
8. [Déploiement App Platform](docs/adr/008-app-platform.md)

</details>

## 📄 Licence

Distribué sous licence **GPL-3.0**. Voir [`LICENSE`](LICENSE).
