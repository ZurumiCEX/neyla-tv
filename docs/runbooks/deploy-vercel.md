# Runbook — Déploiement du frontend sur Vercel

> ⚠ **Vercel n'héberge que le frontend Next.js** (`apps/web`). Le backend
> Django (REST + WebSocket Channels + Celery + Postgres + Redis) **ne peut pas
> tourner sur Vercel** : il doit être déployé ailleurs (DigitalOcean App
> Platform — voir [`deploy-app-platform.md`](deploy-app-platform.md) — ou un
> Droplet via Docker). Vercel appellera ce backend via son URL publique.

## Cause du `404: NOT_FOUND` au premier déploiement

Le repo est un **monorepo** : l'app Next.js est dans `apps/web`, pas à la
racine. Par défaut Vercel build depuis la racine, n'y trouve aucune app Next
et sert un 404. Il faut lui indiquer le bon dossier racine.

## 1. Configurer le projet Vercel

Dans le dashboard Vercel → ton projet → **Settings → Build & Deployment** :

| Réglage | Valeur |
|---------|--------|
| **Root Directory** | `apps/web` ← **le réglage clé** |
| Framework Preset | Next.js (auto-détecté) |
| Build Command | `npm run build` (ou laisser par défaut) |
| Install Command | `npm install` (ou laisser par défaut) |
| Node.js Version | 20.x |

> Le « Root Directory » ne peut **pas** être fixé dans `vercel.json` — c'est un
> réglage du dashboard. Une fois `apps/web` sélectionné, Vercel lit le
> `apps/web/vercel.json` et le `apps/web/package.json`.

Après avoir changé le Root Directory : **Redeploy** (Deployments → ⋯ →
Redeploy) pour que le nouveau réglage prenne effet.

## 2. Variables d'environnement (Settings → Environment Variables)

Le frontend a besoin de connaître l'URL du backend Django.

| Variable | Exemple | Rôle |
|----------|---------|------|
| `NEXT_PUBLIC_API_URL` | `https://api.neyla.tv` | Appels API côté **navigateur** (exposé au client). |
| `API_URL_INTERNAL` | `https://api.neyla.tv` | Appels API côté **serveur** (SSR). URL absolue obligatoire. |

> Si le frontend et l'API sont sur des domaines différents, configure CORS et
> `CSRF_TRUSTED_ORIGINS` côté Django, et `SameSite`/`Secure` sur les cookies de
> refresh pour que l'auth fonctionne cross-site.

⚠ **WebSocket du chat** : Vercel ne proxifie pas les WebSockets vers un backend
externe. Le chat (`/ws/...`) doit pointer directement vers le domaine de l'API
(`wss://api.neyla.tv/ws/...`), pas vers le domaine Vercel.

## 3. Vérifier

1. Ouvre l'URL de production Vercel → la home doit s'afficher (plus de 404).
2. Les listes de lives/catégories se chargent → `NEXT_PUBLIC_API_URL` est bon.
3. Connexion / inscription fonctionnent → cookies cross-site OK.

## Alternative recommandée

Comme le backend doit de toute façon être hébergé hors Vercel, le plus simple
est de **tout déployer sur DigitalOcean App Platform** (frontend + API + jobs)
avec un seul `.do/app.yaml` : `/api` est routé vers le service Django et le
reste vers Next.js, sur la même origine — pas de souci CORS/cookies/WebSocket.
Voir [`deploy-app-platform.md`](deploy-app-platform.md).
