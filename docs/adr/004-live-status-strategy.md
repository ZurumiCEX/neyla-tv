# ADR 004 — Stratégie d'affichage du statut live

- **Statut** : Acceptée
- **Date** : 2026-05-16

## Contexte

La page chaîne `/c/<slug>` doit afficher un badge **EN DIRECT** / **HORS-LIGNE**
qui suit le statut du stream en quasi-temps réel (latence acceptable ~10s).
Deux approches sont possibles : polling HTTP léger, ou WebSocket dédié.

## Décision

On **poll HTTP** un endpoint léger `GET /api/channels/<slug>/status` toutes
les **5 secondes** côté frontend.

- Payload minimal : `{is_live, last_live_started_at}`.
- Cache-Control public 5 s → cacheable côté CDN Cloudflare.
- Auth : AllowAny (info publique).

Pour le compteur viewers : reporté en Phase 4 (sera dérivé du WebSocket
de chat, qui a un compteur naturel par room).

## Conséquences

### Positives
- **Pas de nouvelle connexion WS** à maintenir pour chaque viewer juste
  pour un badge. À 1 000 viewers concurrents on aurait 1 000 connexions
  WebSocket persistantes pour un simple booléen.
- **Caching CDN gratuit** : avec `max-age=5`, Cloudflare absorbe la
  quasi-totalité du trafic. L'API ne voit que 1 requête / 5 s / edge.
- **Code trivial** : `useEffect` + `setInterval` côté front, vue DRF
  classique côté back. Pas de Channels routing, pas de consumer.
- **Robuste** : un viewer qui perd le réseau reprend automatiquement au
  prochain poll. Pas de logique de reconnexion à écrire.

### Négatives / dette
- Latence max ~5 s entre la connexion réelle au RTMPS et la bascule du
  badge. Acceptable au MVP (Twitch a aussi ~5-10 s de lag entre l'ingest
  et l'affichage du badge live).
- Si on a > 100 000 viewers concurrents par chaîne, le poll commencera
  à coûter (même cacheable, il y a la latence et la conn TCP). À ce
  moment-là on basculera sur un WS, mais on ne sera plus en MVP.

## Alternatives écartées

- **WebSocket dédié `/ws/channels/<slug>/status`** : trop coûteux pour
  un seul booléen. On garde le budget WS pour le chat (Phase 4) où c'est
  indispensable.
- **Server-Sent Events** : un peu moins lourd qu'un WS mais toujours
  une connexion par viewer. Mêmes objections.
- **Inclure le statut dans la page SSR seulement** : marche au premier
  load mais ne se met pas à jour. Mauvaise expérience.

## Révision

À revoir quand le chat Phase 4 sera en place : si on a déjà un consumer
Channels par viewer pour le chat, on peut potentiellement piggyback le
statut live dessus et économiser le poll. Mais ce n'est pas urgent, le
poll cacheable scale très loin.
