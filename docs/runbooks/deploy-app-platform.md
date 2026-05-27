# Runbook — Déploiement DigitalOcean App Platform

Déploiement de Neyla TV en PaaS via la spec [`.do/app.yaml`](../../.do/app.yaml).
Pour la topologie et les compromis : [ADR 008](../adr/008-app-platform.md).

> ⚠️ **L'assistant "Create App from source" de la console ne lit PAS la spec.**
> Il fait de l'auto-détection (cherche un manifeste à la racine) et échoue sur
> ce monorepo ("No components detected"). Toujours déployer **à partir de la
> spec** : `doctl apps create --spec ...` (ou Settings → App Spec en console).

## Prérequis

- Compte DigitalOcean + facturation active.
- [`doctl`](https://docs.digitalocean.com/reference/doctl/how-to/install/)
  installé et authentifié : `doctl auth init`.
- Dépôt GitHub `ZurumiCEX/neyla-tv` **connecté** à DigitalOcean
  (Settings → GitHub) pour le `deploy_on_push`.

> 🔒 **Repo privé non lisible par DO ?** Si l'erreur "Make sure we have
> permission to read your repo" persiste malgré l'autorisation de l'app
> GitHub, voir l'[Annexe — Déploiement sans intégration GitHub](#annexe--déploiement-sans-intégration-github).

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

### Base Redis : cluster managé requis

App Platform ne crée pas de **dev DB Redis** (uniquement PG/MySQL). Une base
`production: true` doit donc **référencer un cluster managé déjà créé** :

1. DO → **Databases → Create Database Cluster → Valkey (Redis)**, région **fra**
   (même région que l'app), plus petite taille. Nomme-le (ex. `neyla-redis`).
2. Dans la spec, renseigne `cluster_name:` avec ce nom (placeholder
   `REPLACE_WITH_YOUR_REDIS_CLUSTER_NAME`).

> 💡 **Alternative sans coût (test)** : retirer le bloc `redis` des `databases`
> et pointer `REDIS_URL` / `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` vers un
> Redis externe (ex. Upstash, free tier, URL `rediss://`). Le code gère le TLS.

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

---

## Annexe — Déploiement sans intégration GitHub

Quand DigitalOcean ne peut pas lire le repo privé (erreur *"No components
detected / permission to read your repo"*) et que réautoriser l'app GitHub n'y
change rien, on contourne en clonant une **URL git publique**. La spec
[`.do/app.git.yaml`](../../.do/app.git.yaml) utilise une source `git:` au lieu
de `github:`.

> Compromis : la source `git:` **n'a pas d'auto-deploy sur push**. On redéploie
> à la main (`doctl apps create-deployment <APP_ID>`). Une fois l'accès GitHub
> résolu, repasser à `.do/app.yaml` pour retrouver le `deploy_on_push`.

### Étapes

1. **Rendre le repo public** (temporairement) :
   GitHub → repo → **Settings → General → Danger Zone → Change repository
   visibility → Public**.
   > Les secrets de Neyla TV vivent dans les variables d'environnement, pas
   > dans le code, donc une exposition courte est acceptable. Vérifier malgré
   > tout qu'aucun secret n'a été commité dans l'historique.

2. **Installer `doctl`** (binaire unique, pas besoin de Docker) :
   ```bash
   # macOS
   brew install doctl
   # Linux (snap)
   sudo snap install doctl
   # ou télécharger : https://github.com/digitalocean/doctl/releases
   doctl auth init   # coller un token API DO (read+write)
   ```

3. **Créer l'app depuis la spec git** :
   ```bash
   doctl apps create --spec .do/app.git.yaml
   doctl apps list                          # noter l'APP_ID
   ```

4. **Repasser le repo en privé** une fois le build terminé :
   GitHub → **Settings → General → Change visibility → Private**.
   (L'app reste déployée ; le code est déjà cloné côté DO.)

5. **Redéploiements ultérieurs** (le repo étant repassé privé, il faut le
   remettre public le temps du build, ou résoudre l'accès GitHub et basculer
   sur `.do/app.yaml`) :
   ```bash
   doctl apps create-deployment <APP_ID>
   ```

La suite (secrets, seed, superuser, vérifications) est identique aux sections
1, 3 et 4 ci-dessus.

### Variante console — shim Dockerfile à la racine

Si DO **peut sélectionner** le repo mais l'auto-détection affiche encore "No
components detected" (layout monorepo, aucun manifeste à la racine), un
`Dockerfile` racine sert de "pied dans la porte" :

1. Le repo contient un `Dockerfile` à la racine (shim, identique à l'image API).
   Le wizard détecte alors **un composant**.
2. Crée l'app avec ce composant unique (peu importe qu'il soit incomplet).
3. **Settings → App Spec → Edit** → colle l'intégralité de `.do/app.yaml`
   (qui pointe vers `infra/docker/*.Dockerfile`) → **Save** → topologie complète.
4. Le shim racine n'est plus utile : tu peux le **supprimer** (`git rm Dockerfile`)
   au prochain commit — la spec ne le référence pas.

> ⚠️ Si même avec un `Dockerfile` à la racine le wizard ne détecte rien, c'est
> que DO **n'a réellement pas accès au repo** (permission). Dans ce cas, seules
> les voies "source git publique" (ci-dessus) ou la résolution de l'accès
> GitHub fonctionneront.
