# ADR 003 — Cloudflare Stream pour l'ingestion vidéo

- **Statut** : Acceptée
- **Date** : 2026-05-16

## Contexte

Le MVP doit ingérer le flux RTMP des streamers (OBS) et le servir en HLS aux
viewers. C'est la partie la plus coûteuse et la plus complexe à opérer
soi-même (transcoding multi-bitrate, bande passante, redondance).

## Décision

On utilise **Cloudflare Stream Live Inputs** comme service vidéo :

- Chaque chaîne a un **Live Input** dédié, créé via
  `POST /accounts/<id>/stream/live_inputs`.
- Côté Django on stocke `live_input_uid`, `rtmps_url`, `rtmps_key`,
  `hls_playback_url`.
- Les transitions `is_live` ↔ `not_live` sont déclenchées par les
  **webhooks Cloudflare** (`live_input.connected`, `live_input.disconnected`)
  qu'on reçoit sur `/api/webhooks/cloudflare/stream`.

### Mode FAKE en dev / CI

Si la variable `CLOUDFLARE_API_TOKEN` est vide, le client bascule sur une
implémentation **FAKE** qui retourne des URLs `rtmps://fake.local/...` et
`https://fake.local/<uid>/manifest.m3u8`. Aucun appel réseau n'est fait.
Cela permet :

- de développer toute la stack hors-ligne ;
- de faire tourner la CI sans secret Cloudflare ;
- de valider la chaîne complète (signal → task → DB → API) sans
  dépendance externe.

En prod, on injecte `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` via
les variables d'environnement et le client HTTP réel prend le relais.

### Rotation de la stream key

Pas d'endpoint Cloudflare "régénérer la clé" stable. On adopte la stratégie
**delete + recreate** : on supprime le Live Input et on en recrée un. C'est :

- explicite (l'ancien UID disparaît de Cloudflare) ;
- propre côté CDN (pas de double comptabilité) ;
- forcément interruptif côté streamer (OBS doit être reconfiguré, ce qu'on
  affiche clairement dans le dashboard).

### Signature webhook

Header attendu : `Webhook-Signature: time=<unix>,sig1=<hex>` avec
`sig1 = HMAC-SHA256(secret, f"{time}.{body}")`. Tolérance de fraîcheur :
5 minutes (anti-rejeu). Comparaison via `hmac.compare_digest`. Signature
invalide ou stale → 400 sans détail.

## Conséquences

### Positives
- Zéro infra vidéo à opérer côté DigitalOcean (le poste de coût et de
  complexité le plus lourd est externalisé).
- Lecture HLS via le CDN Cloudflare (latence faible, cache mondial).
- Tarif à l'usage (acceptable au MVP).

### Négatives / dette
- **Vendor lock-in** sur Cloudflare. Sortir = refactor ingest + lecture.
  Acceptable au MVP.
- La clé RTMPS est un **secret sensible**. On ne la sérialise que sur
  `/api/channels/me` (owner authentifié) ; jamais dans les listes.
- Pas de transcoding personnalisé (Cloudflare décide). À revoir si on a
  besoin d'overlays serveur.

## Révision

À revoir si :
- > 5k streamers actifs concurrents (coût Cloudflare Stream à comparer
  avec une stack OBS-side + nginx-rtmp + S3+HLS auto-hébergée).
- Besoin de fonctionnalités vidéo avancées (multi-track audio, sous-titres
  live, watermarks dynamiques).
