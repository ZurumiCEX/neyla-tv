# ADR 008 — Déploiement DigitalOcean App Platform

- **Statut** : Acceptée
- **Date** : 2026-05-26
- **Complète** : [ADR 007 — Déploiement prod (Droplet)](007-prod-deployment.md)

## Contexte

L'ADR 007 décrit un déploiement mono-Droplet + Docker Compose + nginx +
Cloudflare. Ça marche mais demande de l'ops : provisionnement de la machine,
durcissement SSH, ufw, gestion des backups, supervision du disque.

On veut une option **PaaS** sur DigitalOcean **App Platform** : moins d'ops,
scaling déclaratif, bases managées, TLS et ingress gérés par la plateforme.
Objectif : pouvoir lancer la plateforme depuis un simple fichier de spec.

## Décision

### Spec versionnée : `.do/app.yaml`

Toute la topologie est décrite dans `.do/app.yaml` (déployable via
`doctl apps create --spec .do/app.yaml`) :

- **2 services HTTP** : `api` (Django/Daphne) et `web` (Next.js standalone).
- **2 workers** : `worker` et `beat` (Celery).
- **1 job PRE_DEPLOY** : `migrate` (`manage.py migrate --noinput`).
- **2 bases managées** : Postgres 16 + Redis 7 (TLS).

### Routing par chemin (pas de nginx)

L'ingress App Platform route par préfixe, le plus spécifique gagne :

- `api` ← `/api`, `/admin`, `/ws`, `/django-static`
- `web` ← `/` (catch-all)

WebSocket (`/ws`) supporté nativement par la plateforme.

### Statiques : WhiteNoise au lieu de nginx

Sans nginx, Django doit servir ses propres statiques (admin, DRF). On ajoute
**WhiteNoise** (middleware + `CompressedManifestStaticFilesStorage`) et on
exécute `collectstatic` **au build** de l'image (`api.Dockerfile`). Les
statiques Django passent sous `/django-static/` pour ne pas entrer en
collision avec les assets Next.js (`/_next/...`).

### Bases managées + TLS

- **Postgres** : liaison `${db.*}` → variables `POSTGRES_*`, `sslmode=require`.
- **Redis** : `${redis.DATABASE_URL}` (schéma `rediss://`). Le code normalise
  l'URL (`ssl_cert_reqs=none` pour redis-py / channels-redis ; dict
  `CELERY_*_USE_SSL` pour Celery). On chiffre sans vérifier la CA privée :
  acceptable pour du trafic interne au datacenter.

### Frontend même origine

`NEXT_PUBLIC_API_URL = ${APP_URL}` (figé au build via build-arg dans
`web.Dockerfile`). Le navigateur appelle `/api` et `/ws` sur la même origine,
routés vers le service `api`. Le SSR utilise `API_URL_INTERNAL = ${APP_URL}`.

### Hosts & CSRF

`DJANGO_ALLOWED_HOSTS = ${APP_DOMAIN},.ondigitalocean.app` (le wildcard couvre
le domaine par défaut utilisé par les health checks). `CSRF_TRUSTED_ORIGINS =
${APP_URL}` pour l'admin derrière HTTPS. En l'absence de la variable au
runtime, `ALLOWED_HOSTS=[]` → **fail-closed** (et permet le `collectstatic`
au build sans host).

## Conséquences

### Positives
- **Moins d'ops** : pas de machine à durcir, TLS/ingress/scaling gérés.
- **Reproductible** : toute la prod tient dans un fichier versionné.
- **Bases managées** : backups Postgres automatiques côté DO, pas de cron maison.
- **Deploy on push** : redeploy automatique sur push de la branche suivie.

### Négatives / dette
- **Coût** : Redis n'a pas de tier "dev" → noeud managé (~15 USD/mois). Total
  attendu plus élevé que le Droplet (≈ 40-60 USD/mois selon les tailles).
- **Build par composant** : l'image API est rebuildée pour `api`, `worker`,
  `beat`, `migrate` (pas de registry partagé). Builds plus longs/coûteux.
- **`ssl_cert_reqs=none`** : on ne vérifie pas la chaîne CA du Redis managé.
  Mitigation possible : fournir `${redis.CA_CERT}` et passer à `required`.
- **Lock-in modéré** : la spec est spécifique à App Platform (mais l'app
  reste portable : ce sont les mêmes Dockerfiles que le Droplet).

## Alternatives écartées

- **Garder uniquement le Droplet (ADR 007)** : conservé comme option, mais
  plus d'ops. Les deux chemins coexistent (mêmes Dockerfiles).
- **Redis en composant interne** (au lieu de managé) : App Platform ne route
  que le HTTP entre composants ; un Redis TCP interne n'est pas supporté
  proprement → base managée requise.
- **Kubernetes (DOKS)** : sur-dimensionné pour le MVP.

## Révision

À revoir si :
- Le coût Redis managé devient un frein → réévaluer Droplet ou Redis externe.
- Besoin de vérification stricte du certificat → intégrer `${redis.CA_CERT}`.
- Montée en charge → augmenter `instance_count` / `instance_size_slug` dans
  la spec, activer l'autoscaling.
