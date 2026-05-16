# ADR 007 — Déploiement production (mono-Droplet + Compose)

- **Statut** : Acceptée
- **Date** : 2026-05-16

## Contexte

Phase 6 : passer en production. On a une stack Docker Compose qui marche en
dev. Il faut maintenant : un host, une stratégie de deploy, du TLS, des
backups, un peu d'observabilité. Sans exploser le budget MVP (< 30 USD/mois).

## Décision

### Topologie : un seul Droplet, tout sur Compose

- DigitalOcean Droplet Ubuntu 24 LTS, 2 vCPU / 4 Go RAM, Francfort.
- Docker Compose v2 pour orchestrer 7 services : `nginx`, `web`, `api`,
  `worker`, `beat`, `postgres`, `redis`, `backup`.
- Pas de Kubernetes, pas de registry privé, pas d'orchestrateur externe.

### Entrée HTTP : Cloudflare + nginx

- Cloudflare en proxy orange + Pro : termine TLS, cache statique, WAF,
  rate-limit. Le Droplet n'expose que le port 80.
- nginx local sert d'entrée unique :
  - `/api/`, `/admin/`, `/static/` → conteneur `api` (Daphne ASGI).
  - `/ws/` → conteneur `api`, avec upgrade WebSocket + masquage de la
    query string dans les access logs (cf. ADR 005 §JWT en query param).
  - tout le reste → conteneur `web` (Next.js standalone).

### Deploy : git pull sur le Droplet via SSH

- Workflow GitHub Actions `deploy.yml` (push `main` → `appleboy/ssh-action`).
- Étapes sur le Droplet : `git pull --ff-only`, `docker compose build`,
  `up -d`, `migrate --noinput`, `system prune -f`.
- Pas de registry : on construit sur la machine. Build incremental Docker
  prend ~30 s en steady-state.
- Verrou de concurrence : `concurrency: deploy-prod cancel-in-progress: false`.

### Images : multi-stage Dockerfiles

- `api.Dockerfile` cible `dev` (avec pytest/linters) ou `prod` (uniquement
  prod deps, user non-root, settings prod).
- `web.Dockerfile` cible `dev` (`next dev`) ou `prod` (build `output: standalone`,
  image runtime ~120 Mo).
- `nginx.Dockerfile` minimal : `nginx:alpine` + notre conf.

### Backups Postgres : conteneur cron + DO Spaces

- Service Compose `backup` : `postgres:16-alpine` + `aws-cli` + `crond`.
- Cron quotidien 03:00 UTC → `pg_dump | gzip | aws s3 cp`.
- Rétention : lifecycle rule 30 jours sur le bucket Spaces (plus fiable
  qu'un nettoyage scripté).
- Runbook `restore-postgres.md` documenté.

### Observabilité

- **Sentry** (server-only au MVP) : init dans `prod.py` si `SENTRY_DSN` posé.
  Couvre Django + Celery. Frontend Sentry **reporté** (config Next non
  triviale, on l'ajoutera si on a des bugs front non reproductibles).
- **Logs JSON** en prod : formatter custom dans `prod.py`. Facilite
  l'agrégation future (Logpush, syslog).
- **Healthchecks** :
  - `/healthz` nginx → 200 statique (LB Cloudflare).
  - `/api/healthz` Django → ping DB + Redis (détecte panne backend).

## Conséquences

### Positives
- **Coût** : < 30 USD/mois (Droplet 24 + Spaces ~1 + Cloudflare gratuit).
- **Simplicité opérationnelle** : `git pull && docker compose up -d`.
  Un nouveau dev peut tout reproduire en 30 min depuis les runbooks.
- **Pas de lock-in** : Droplet remplaçable, Compose portable, Spaces
  compatible S3 standard.
- **Sécurité par défaut** : ufw 22/80 seulement, secrets en `.env` (chmod
  600), TLS Cloudflare, refresh cookie Secure + HttpOnly + SameSite=Lax.

### Négatives / dette
- **SPOF mono-Droplet** : si le host crash, tout est down. Acceptable
  pre-PMF, intolérable post-traction. Roadmap : ajouter un second Droplet
  + load balancer + Postgres managé une fois MRR > 500 USD.
- **Pas de registry** : si le Droplet ne peut plus build (réseau down),
  pas de deploy possible. Mitigation : tag git stable + clone localement
  pour debug.
- **Logs Docker locaux** : si le disque sature, les logs sont perdus.
  Limite `log-driver: json-file` + `max-size` à configurer en
  `daemon.json` au provisionnement (à inclure dans le runbook).
- **Backups uniquement Postgres** : Redis (chat messages éphémères) et
  les Live Inputs Cloudflare (gérés côté CF) ne sont pas backupés. C'est
  voulu.

## Alternatives écartées

- **Cloud managé (Render / Fly.io / Railway)** : 3-5× plus cher au MVP,
  moins de contrôle, dépendance forte.
- **Kubernetes (DOKS / k3s)** : énorme over-engineering pour 1 service.
- **Registry tiers (GHCR / Docker Hub)** : étape de build CI + push +
  pull sur le Droplet. Pas de bénéfice tant qu'on a un seul host.
- **Sentry frontend dès le MVP** : config Next 14 non triviale, coût
  bundle, pas de retour utilisateur tant qu'on n'a pas une vraie base.

## Révision

À revoir quand :
- MRR > 500 USD : provisionner un 2e Droplet + Postgres managé +
  load balancer + registry partagé.
- > 5 000 viewers concurrents : tasser Daphne / Redis ou multiplier les
  workers.
- Apparition de pannes Sentry impossibles à reproduire en local :
  brancher Sentry frontend.
