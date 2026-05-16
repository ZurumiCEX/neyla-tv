# Neyla TV

MVP de plateforme de streaming jeux vidéo (type Twitch / Kick).
Stack figée dans [`docs/adr/001-stack-mvp.md`](docs/adr/001-stack-mvp.md).

## Prérequis

- Docker + Docker Compose v2
- `make`
- Git

## Démarrage rapide

```bash
cp .env.example .env
make up          # build + démarre tous les services
make migrate     # applique les migrations Django
make logs        # suivi des logs
```

Une fois les services up :

| Service   | URL                              |
|-----------|----------------------------------|
| Frontend  | http://localhost:3000            |
| API       | http://localhost:8000/api/healthz |
| Admin     | http://localhost:8000/admin/     |
| Postgres  | localhost:5432                   |
| Redis     | localhost:6379                   |

La page d'accueil affiche l'état de l'API, Postgres et Redis.

## Commandes utiles

| Commande         | Effet                                          |
|------------------|------------------------------------------------|
| `make up`        | Build + démarre tous les services en arrière-plan |
| `make down`      | Stoppe et supprime les conteneurs              |
| `make logs`      | Logs en suivi (Ctrl+C pour quitter)            |
| `make migrate`   | Applique les migrations Django                 |
| `make shell`     | Shell Django dans le conteneur API             |
| `make test`      | Lance pytest (API)                             |
| `make lint`      | Ruff + Black --check + ESLint                  |
| `make format`    | Auto-fix (Ruff, Black, isort, Prettier)        |

## Structure

```
apps/
  api/                 # Django 5 (accounts, channels_app, chat, catalog, social, health)
  web/                 # Next.js 14 (App Router, Tailwind)
infra/
  docker/              # Dockerfiles api + web + nginx + backup (multi-stage dev/prod)
  compose/             # docker-compose.yml (dev) + docker-compose.prod.yml
  nginx/               # config nginx prod
  scripts/             # backup-postgres.sh
docs/
  adr/                 # Architecture Decision Records (001 → 007)
  runbooks/            # deploy, restore-postgres, incident-response, cloudflare-webhooks
```

## Premières étapes après bootstrap

1. Créer un superuser : `docker compose -f infra/compose/docker-compose.yml exec api python manage.py createsuperuser`
2. Charger le seed des jeux : `docker compose -f infra/compose/docker-compose.yml exec api python manage.py loaddata catalog/fixtures/games_seed.json`
3. Ouvrir http://localhost:8000/admin/ et vérifier le login.
4. Vérifier la home http://localhost:3000 : pastilles santé vertes attendues.

## Production

- **Topologie** : un Droplet DigitalOcean + Docker Compose, Cloudflare en
  proxy orange (TLS + WAF). Détails et compromis dans
  [`docs/adr/007-prod-deployment.md`](docs/adr/007-prod-deployment.md).
- **Deploy** : automatique sur push `main` via GitHub Actions SSH.
  Étape-par-étape dans [`docs/runbooks/deploy.md`](docs/runbooks/deploy.md).
- **Backups** : dump Postgres quotidien vers DigitalOcean Spaces.
  Restauration : [`docs/runbooks/restore-postgres.md`](docs/runbooks/restore-postgres.md).
- **Incident** : checklist 5 min dans
  [`docs/runbooks/incident-response.md`](docs/runbooks/incident-response.md).

## ADR

1. [`001-stack-mvp.md`](docs/adr/001-stack-mvp.md) — Stack figée
2. [`002-jwt-strategy.md`](docs/adr/002-jwt-strategy.md) — JWT + refresh cookie
3. [`003-cloudflare-stream.md`](docs/adr/003-cloudflare-stream.md) — Cloudflare Stream + mode FAKE
4. [`004-live-status-strategy.md`](docs/adr/004-live-status-strategy.md) — Poll HTTP pour le badge LIVE
5. [`005-chat-architecture.md`](docs/adr/005-chat-architecture.md) — Chat Redis-only + JWT query param
6. [`006-discovery-and-social.md`](docs/adr/006-discovery-and-social.md) — Follow, découverte, recherche
7. [`007-prod-deployment.md`](docs/adr/007-prod-deployment.md) — Déploiement prod
