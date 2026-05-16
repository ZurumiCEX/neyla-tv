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
  api/         # Django 5 (config, accounts, health)
  web/         # Next.js 14 (App Router, Tailwind)
infra/
  docker/      # Dockerfiles api + web
  compose/     # docker-compose.yml dev
  nginx/       # confs nginx (Phase 6)
docs/
  adr/         # Architecture Decision Records
  runbooks/    # Procédures ops
```

## Premières étapes après bootstrap

1. Créer un superuser : `docker compose -f infra/compose/docker-compose.yml exec api python manage.py createsuperuser`
2. Ouvrir http://localhost:8000/admin/ et vérifier le login.
3. Vérifier la home http://localhost:3000 : 3 pastilles vertes attendues.

## Phases suivantes

Le découpage et les périmètres sont décrits dans le prompt projet
(Phase 1 → auth, Phase 2 → Cloudflare Stream, etc.). À chaque phase :
plan validé → code → tests verts → ADR éventuel → démo locale.
