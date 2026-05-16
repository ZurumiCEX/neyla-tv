# ADR 001 — Stack technique du MVP

- **Statut** : Acceptée
- **Date** : 2026-05-16

## Contexte

On lance un MVP de plateforme de streaming jeux vidéo (type Twitch / Kick).
Contraintes : sortir vite, budget < 30 USD / mois, une seule personne dev au
démarrage, scalabilité raisonnable sans réécriture.

## Décision

On fige la stack suivante :

| Couche         | Choix                                  |
|----------------|----------------------------------------|
| Frontend       | Next.js 14 (App Router, TypeScript), `hls.js` côté player |
| Backend        | Django 5 (Python 3.12) en mode ASGI (Daphne) |
| API HTTP       | Django REST Framework + `djangorestframework-simplejwt` |
| Realtime       | Django Channels (WebSocket) |
| Tâches async   | Celery + Celery Beat |
| Cache / broker | Redis 7 (channel layer, Celery, cache) |
| Base de données| PostgreSQL 16 |
| Vidéo          | Cloudflare Stream (Live Inputs, ingestion RTMP, lecture HLS) |
| Infra          | DigitalOcean Droplet Ubuntu 24, Docker Compose |
| CDN / WAF      | Cloudflare (proxy orange, Pro) |
| CI/CD          | GitHub Actions (lint + tests sur PR, deploy SSH en Phase 6) |

## Conséquences

- **Positives** : stack mainstream, beaucoup de docs, recrutement facile,
  coûts maîtrisés, pas de lock-in cloud lourd. Cloudflare Stream sort le sujet
  vidéo le plus dur (ingestion + transcoding + lecture HLS).
- **Négatives / dette** :
  - Pas de Kubernetes : si on doit scaler horizontalement, il faudra
    refactor l'infra (Phase post-MVP).
  - Dépendance forte à Cloudflare Stream (vendor lock-in vidéo). Acceptable
    pour le MVP.
  - Single Droplet = SPOF. On accepte le risque tant qu'on est en
    pré-product-market-fit.

## Révision

À revoir une fois > 1000 streamers actifs ou > 50k viewers simultanés.
