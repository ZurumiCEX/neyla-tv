# Runbook — API sur Fly.io + Neon (Postgres) + Upstash (Redis)

Le front reste sur **Vercel** ([`deploy-vercel.md`](deploy-vercel.md)). Ce guide
héberge le reste :

| Brique | Où | Rôle |
|---|---|---|
| API Django (Daphne, HTTP + WebSocket du chat) | Fly.io, groupe `app` | `/api/…`, `/ws/…`, `/admin/` |
| Worker Celery | Fly.io, groupe `worker` | tâches de fond (e-mails, Bunny…) |
| Celery beat | Fly.io, groupe `beat` | tâches planifiées (statut live, renouvellements) |
| PostgreSQL | Neon | base de données |
| Redis | Upstash | chat temps réel, cache des limites anti-abus, file Celery |

La configuration Fly est dans [`fly.toml`](../../fly.toml), à la racine du dépôt.

**Coût indicatif** : Fly ~5–10 $/mois (3 petites machines), Neon gratuit au
départ, Upstash ~0–10 $/mois (voir l'avertissement en 2).

---

## 1. Postgres sur Neon

1. Crée un compte sur [neon.tech](https://neon.tech), puis un projet en région
   **AWS Europe Central (Frankfurt)**, la plus proche de Paris.
2. Dans **Connection Details**, **décoche** « Pooled connection » et copie l'URL
   **directe** (sans `-pooler` dans le nom d'hôte) :
   `postgresql://user:motdepasse@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require`
   L'URL directe est la plus fiable pour les migrations et les connexions
   persistantes de Django. `&channel_binding=require` (ajouté par Neon) est accepté.

C'est ton `DATABASE_URL`. L'API la lit en priorité sur les variables `POSTGRES_*`.

## 2. Redis sur Upstash

Au choix :

- **Depuis Fly** (le plus simple, facturé par Fly) : `fly redis create`, région `cdg` ;
- **Depuis [upstash.com](https://upstash.com)** : base Redis en région `eu-west-3` (Paris).

Copie l'URL **TLS** : `rediss://default:motdepasse@xxx.upstash.io:6379`.

> ⚠ **Celery interroge Redis en permanence.** L'offre gratuite d'Upstash
> (500 000 commandes par mois) est épuisée en quelques jours. Prends l'offre
> **Pay as you go** (ou un plan fixe), sinon le chat et les tâches s'arrêtent
> quand le quota est atteint.

Upstash ne propose qu'une seule base (`/0`) : la même URL sert pour le cache,
le chat et Celery.

## 3. Créer l'app Fly

```bash
# Installer flyctl : https://fly.io/docs/flyctl/install/
fly auth login
fly launch --no-deploy --copy-config --name neyla-tv   # garde le fly.toml du dépôt
```

Si le nom `neyla-tv` est déjà pris, choisis-en un autre et change **seulement**
la ligne `app` de `fly.toml` : le domaine `<app>.fly.dev` est autorisé
automatiquement. Remplace aussi `neyla-tv` dans les commandes ci-dessous.

## 4. Secrets

Remplace les valeurs entre `<…>`. `<prod>` est le domaine de ton site Vercel.

```bash
fly secrets set \
  DJANGO_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')" \
  DATABASE_URL="<url Neon>" \
  REDIS_URL="<url Upstash rediss://…>" \
  CELERY_BROKER_URL="<url Upstash rediss://…>" \
  CELERY_RESULT_BACKEND="<url Upstash rediss://…>" \
  DJANGO_CORS_ALLOWED_ORIGINS="https://<prod>.vercel.app" \
  DJANGO_CORS_ALLOWED_ORIGIN_REGEXES='^https://neyla-tv-.*\.vercel\.app$' \
  FRONTEND_URL="https://<prod>.vercel.app" \
  WEBAUTHN_RP_ID="<prod>.vercel.app" \
  WEBAUTHN_ORIGINS="https://<prod>.vercel.app" \
  SEED_DEMO=1
```

- `DJANGO_CORS_ALLOWED_ORIGIN_REGEXES` autorise toutes les URL de preview
  Vercel. Adapte le préfixe (`neyla-tv-`) au nom de ton projet Vercel.
- `SEED_DEMO=1` crée les comptes démo à chaque déploiement, sans rien effacer.
- `WEBAUTHN_RP_ID` / `WEBAUTHN_ORIGINS` : domaine **du front** pour les passkeys.
  Une passkey créée sur un domaine ne fonctionne que sur ce domaine : les
  previews Vercel (autres domaines) ne peuvent pas les utiliser, c'est normal.
- `REQUIRE_STAFF_2FA` (dans `fly.toml`, `0` pour la démo) : à passer à `1` en
  production réelle. Les comptes admin / modo / support devront alors activer
  la 2FA ou une passkey (**Paramètres → Authentification**) avant d'ouvrir la
  console.

Optionnel, mêmes noms que dans [`.env.example`](../../.env.example) :

- **Vidéo** : `BUNNY_STREAM_LIBRARY_ID`, `BUNNY_STREAM_API_KEY`,
  `BUNNY_STREAM_CDN_HOSTNAME`, `BUNNY_STREAM_WEBHOOK_KEY` (sinon mode FAKE) ;
- **E-mails** : `DJANGO_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`,
  `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` ;
- **Anti-robots** : `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY` ;
- **Erreurs** : `SENTRY_DSN`.

## 5. Déployer

```bash
fly deploy
fly scale count app=1 worker=1 beat=1
```

À chaque `fly deploy`, la `release_command` (`apps/api/scripts/release.sh`)
vérifie les secrets et la connexion à la base, applique les migrations puis,
si `SEED_DEMO=1`, lance `seed_demo`. Chaque étape est écrite dans les logs. **Garde une seule machine `beat`**, sinon les
tâches planifiées s'exécutent en double.

## 6. Brancher Vercel

Vercel → ton projet → **Settings → Environment Variables** :

| Variable | Valeur |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://neyla-tv.fly.dev` |
| `API_URL_INTERNAL` | `https://neyla-tv.fly.dev` |

Puis **Deployments → ⋯ → Redeploy**. `NEXT_PUBLIC_*` est figé au build : un
redéploiement est obligatoire. Le chat se connecte alors en
`wss://neyla-tv.fly.dev/ws/…`.

## 7. Vérifier

```bash
curl https://neyla-tv.fly.dev/api/livez     # {"status": "ok"}
curl https://neyla-tv.fly.dev/api/healthz   # db + redis "ok"
fly logs                                     # en cas d'erreur
fly ssh console -C "python manage.py reconcile_wallets"
```

Sur le site Vercel, connecte-toi avec `admin@demo.neyla.tv` / `DemoPass2026!`.
La console est sur `/console/dashboard`. Recharge la page : tu dois rester connecté.

Pour créer ton propre compte admin :

```bash
fly ssh console -C "python manage.py createsuperuser"
```

## Dépannage du premier déploiement

**« Failed to provision IP addresses … org_slug is only supported with
private_v6 type »** : bug connu de flyctl au premier déploiement, sans lien avec
le code. Mets flyctl à jour et attribue les adresses à la main :

```bash
fly version update
fly ips allocate-v6 -a neyla-tv
fly ips allocate-v4 --shared -a neyla-tv
fly ips list -a neyla-tv
```

**« release_command failed … exit code 1 »** (souvent avec « timeout waiting
for release command logs ») : la vérification ou les migrations ont échoué.
Le plus rapide est le diagnostic, qui s'affiche **directement dans ton
terminal** et n'écrit rien. Prends le tag `deployment-…` affiché par `fly deploy` :

```bash
fly machine run registry.fly.io/neyla-tv:deployment-<tag> \
  sh /app/scripts/diagnose.sh --rm -a neyla-tv
```

Il liste chaque secret (« défini » / « absent », jamais la valeur), teste la
base et Redis, puis montre les migrations en attente. Autres pistes :

```bash
fly logs -a neyla-tv --no-tail   # en cas d'échec, la release attend 15 s pour que ses logs arrivent
fly secrets list -a neyla-tv     # noms des secrets de CETTE app
```

Un `fly secrets set` ne compte qu'au déploiement suivant, et doit viser la bonne
app (`-a neyla-tv`).

Messages possibles :

| Message | Correction |
|---|---|
| `secret(s) manquant(s) : DJANGO_SECRET_KEY` | `fly secrets set DJANGO_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"` |
| `secret(s) manquant(s) : DATABASE_URL` | `fly secrets set DATABASE_URL="<URL directe Neon>"` |
| `Connexion à la base impossible` | URL Neon erronée, mot de passe changé, ou URL « -pooler » : reprends l'URL directe. |
| `seed_demo a échoué` | Démo seulement, le déploiement continue ; vérifie `PAYMENTS_ALLOW_FAKE=1`. |

Secrets minimum avant `fly deploy` : `DJANGO_SECRET_KEY`, `DATABASE_URL`,
`REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`,
`DJANGO_CORS_ALLOWED_ORIGINS`, `FRONTEND_URL`, `WEBAUTHN_RP_ID`, `WEBAUTHN_ORIGINS`.

## Dépannage

| Symptôme | Cause probable |
|---|---|
| « Identifiants invalides » avec les comptes démo | `SEED_DEMO` n'était pas à `1` au déploiement. Lance `fly ssh console -C "python manage.py seed_demo"`. |
| Connecté, puis déconnecté au rechargement | Le cookie de refresh doit être `SameSite=None` (déjà dans `fly.toml`), et l'origine Vercel doit être dans les variables CORS. |
| « Impossible de joindre le serveur » | `NEXT_PUBLIC_API_URL` faux, ou Vercel pas redéployé après le changement. |
| Erreur `400 Bad Request` sur l'API | Domaine personnalisé non déclaré : ajoute-le avec `fly secrets set DJANGO_ALLOWED_HOSTS=api.mondomaine.com` (`<app>.fly.dev` est déjà autorisé). |
| Chat muet, tâches bloquées | Quota Upstash atteint : voir l'avertissement en 2. |

Quand la démo n'est plus nécessaire : `fly secrets set SEED_DEMO=0`. Pour encaisser
réellement, passe `PAYMENTS_ALLOW_FAKE` à `0` dans `fly.toml` et configure
Stripe, Wave et Orange Money.
