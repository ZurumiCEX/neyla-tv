# Runbook — Déploiement DigitalOcean App Platform

Déploiement de Neyla TV en PaaS via la spec [`.do/app.yaml`](../../.do/app.yaml).
Pour la topologie et les compromis : [ADR 008](../adr/008-app-platform.md).

## Prérequis

- Compte DigitalOcean + facturation active.
- [`doctl`](https://docs.digitalocean.com/reference/doctl/how-to/install/)
  installé et authentifié : `doctl auth init`.
- Dépôt GitHub `ZurumiCEX/neyla-tv` **connecté** à DigitalOcean
  (Settings → GitHub) pour le `deploy_on_push`.

## 1. Préparer les secrets

Avant la première création, éditer `.do/app.yaml` ou prévoir de surcharger
en console :

| Variable | Valeur | Note |
|----------|--------|------|
| `DJANGO_SECRET_KEY` | aléatoire ≥ 50 car. | `python -c "import secrets;print(secrets.token_urlsafe(64))"` |
| `CLOUDFLARE_ACCOUNT_ID` | depuis Cloudflare | vide = mode FAKE (pas de live réel) |
| `CLOUDFLARE_API_TOKEN` | token Stream:Edit | idem |
| `CLOUDFLARE_WEBHOOK_SECRET` | secret partagé | doit matcher la config du webhook CF |
| `SENTRY_DSN` | optionnel | vide = Sentry désactivé |

> Les variables liées aux bases (`POSTGRES_*`, `REDIS_URL`, `CELERY_*`) sont
> renseignées **automatiquement** via les liaisons `${db.*}` / `${redis.*}`.
> Ne pas les surcharger manuellement.

## 2. Créer l'app

```bash
doctl apps create --spec .do/app.yaml
# Récupérer l'APP_ID :
doctl apps list
```

DigitalOcean provisionne les bases managées (Postgres + Redis), build les
images (api, web, workers), exécute le job `migrate` (PRE_DEPLOY) puis démarre
les services.

## 3. Données initiales (one-time)

Via la console (Component `api` → **Console**) ou `doctl apps console` :

```bash
# Charger le seed des jeux
python manage.py loaddata catalog/fixtures/games_seed.json
# Créer un superuser admin
python manage.py createsuperuser
```

## 4. Vérifications post-deploy

```bash
APP_URL=$(doctl apps get <APP_ID> --format DefaultIngress --no-header)
curl -sS "$APP_URL/api/healthz"          # {"status":"ok","db":true,"redis":true}
```

1. `GET $APP_URL/api/healthz` → `status: ok`.
2. Ouvrir `$APP_URL/` : la home charge, les pastilles santé sont vertes.
3. `$APP_URL/admin/` : le **CSS de l'admin se charge** (= WhiteNoise OK).
4. Page chaîne `/c/<slug>` : le chat se connecte (WebSocket `/ws` OK).

## 5. Mises à jour

- **Automatique** : push sur `main` → `deploy_on_push` redéploie.
- **Spec modifiée** :
  ```bash
  doctl apps update <APP_ID> --spec .do/app.yaml
  ```

## 6. Domaine custom (optionnel)

Console → app → **Settings → Domains** → ajouter `app.<domaine>`. App Platform
gère le certificat TLS. `${APP_DOMAIN}` / `${APP_URL}` se mettent à jour ;
`ALLOWED_HOSTS` inclut déjà le domaine principal.

## Dépannage

| Symptôme | Cause probable | Fix |
|----------|----------------|-----|
| `400 Bad Request` (DisallowedHost) | `ALLOWED_HOSTS` ne couvre pas le host | Vérifier `DJANGO_ALLOWED_HOSTS=${APP_DOMAIN},.ondigitalocean.app` |
| Admin sans CSS | `collectstatic` non joué / mauvaise route | Vérifier le build de l'image + route `/django-static` |
| `redis ... SSL: CERTIFICATE_VERIFY_FAILED` | TLS Redis mal géré | L'URL doit être `rediss://` (la normalisation ajoute `ssl_cert_reqs=none`) |
| `health: redis=false` | Redis pas joignable | Vérifier que la base `redis` est attachée et `REDIS_URL` liée |
| Migrations non appliquées | job `migrate` échoué | Voir les logs du job `migrate` (PRE_DEPLOY) |
| CSRF 403 sur l'admin | origine non fiable | `DJANGO_CSRF_TRUSTED_ORIGINS=${APP_URL}` |

## Rollback

Console → app → **Activity** → sélectionner un déploiement antérieur →
**Rollback**. Pour un rollback de migration DB, préférer `git revert` du commit
fautif + redeploy (cf. [restore-postgres.md](restore-postgres.md) si dump requis).
