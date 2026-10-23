# ADR 010 — Bunny Stream, unique fournisseur vidéo

- **Statut** : Acceptée — remplace [ADR 003](003-cloudflare-stream.md)
- **Date** : 2026-10-23

## Contexte

La plateforme ingère le flux RTMP des streamers (OBS) et le diffuse en HLS. Elle
publie aussi des vidéos courtes (« Instant » / Shorts). Jusqu'ici, le live passait
par Cloudflare Stream, et l'accueil intégrait des vidéos YouTube.

Deux fournisseurs vidéo, c'est deux intégrations à maintenir, deux facturations et
deux comportements de lecteur. L'équipe a choisi **Bunny Stream** pour tout le
périmètre vidéo. Bunny est économique, possède un CDN mondial avec des points de
présence en Afrique, et sait servir le live (Stream Live, activé sur le compte)
comme la VOD.

## Décision

**Bunny Stream est le seul fournisseur vidéo.** Cloudflare Stream et les intégrations
YouTube sont retirés du code. Cloudflare reste utilisé pour d'autres usages qui ne
sont pas de la vidéo : R2 pour les uploads, Turnstile pour le captcha, CDN/WAF.

| Usage | Mécanisme Bunny |
|-------|-----------------|
| Live d'une chaîne | 1 live stream par chaîne, créé à l'approbation du streamer (`POST /library/{id}/live`) |
| Lecture | HLS servie par le CDN de la bibliothèque (`https://<cdn>/<id>/playlist.m3u8`) |
| État live/offline | **Polling** (`GET /library/{id}/live/{streamId}`) via Celery beat, toutes les `STREAM_STATUS_POLL_SECONDS` |
| Shorts (« Instant ») | Vidéo VOD créée côté API, upload **TUS direct navigateur → Bunny** avec une signature `sha256(library + key + expiry + videoId)` |
| Fin d'encodage VOD | Webhook `POST /api/webhooks/bunny/stream`, signé `X-BunnyStream-Signature` (HMAC-SHA256 du corps) |

### Modèle de données

Les champs de `Channel` portent désormais des noms neutres vis-à-vis du fournisseur :
`stream_id`, `ingest_url`, `stream_key`, `playback_url` et `stream_checked_at`. Ils
ont été renommés par la migration `channels_app/0008`. « Être streamer » se teste par
un unique helper, `channels_app.utils.is_streamer(user)`, qui fait une requête
fraîche.

### Pourquoi le polling

Bunny ne documente pas de webhook d'état live. La synchronisation par polling :

- reste fiable si un événement est perdu, car une chaîne ne reste jamais « coincée
  en live » ;
- se répartit sur les passages, les chaînes les moins récemment vérifiées passant
  d'abord, par lots de 200 ;
- coexiste avec la bascule manuelle « Passer en direct » du dashboard. Celle-ci est
  réservée aux chaînes provisionnées et sert de repli.

Le webhook accepte aussi, sans garantie, d'éventuels événements live
(`LiveStreamId` + `State`) au cas où Bunny en émettrait.

### Mode FAKE

Le client FAKE s'active quand `BUNNY_STREAM_API_KEY` est vide. Il ne fait aucun appel
réseau et renvoie un flux HLS public de test, si bien que le lecteur joue réellement
en démo et en CI. Le polling y est désactivé.

## Conséquences

- **+** Un seul fournisseur, un seul lecteur (hls.js) et un seul jeu de secrets.
- **+** Le live et les Shorts partagent la même bibliothèque, le même CDN et la même facturation.
- **−** La bascule live est détectée avec un retard de l'ordre de
  `STREAM_STATUS_POLL_SECONDS` (20 s par défaut). Le bouton manuel compense pour le
  streamer.
- **−** Le schéma de réponse de l'API live est peu documenté. L'analyse est
  défensive, et `manage.py verify_bunny_stream` affiche la réponse brute pour
  ajuster le code en une ligne si besoin.
- Les secrets passent de `CLOUDFLARE_*` à `BUNNY_STREAM_*` (voir
  [runbook](../runbooks/bunny-stream-setup.md)).
