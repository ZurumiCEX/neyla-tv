# ADR 005 — Architecture du chat live

- **Statut** : Acceptée
- **Date** : 2026-05-16

## Contexte

Le chat est un composant central de l'expérience streaming. Au MVP on doit
gérer : auth, anti-spam, modération streamer, historique court, viewers
count, et un comportement raisonnable pour quelques milliers de connexions
concurrentes.

## Décision

### Transport
- **Django Channels** (déjà dans la stack) avec un `AsyncJsonWebsocketConsumer`.
- Route : `/ws/c/<slug>/chat`.
- Channel layer Redis en prod (déjà configuré), in-memory en tests.

### Authentification WebSocket
- **JWT en query param** : `?token=<access>`. C'est explicite, simple,
  cross-origin friendly, et fonctionne sans bidouille de headers WS côté
  navigateur.
- Anonymes autorisés en **lecture** (regarder le chat).
- L'envoi de message exige un token valide.
- Risques : le query param peut fuiter dans des logs d'access. Mitigations :
  - Access token de 15 min seulement (cf. ADR 002).
  - nginx en prod : log `request_uri` sans query string sur ce path.

### Stockage des messages
- **Pas de DB pour les messages** : on garde uniquement les **100 derniers
  par chaîne** dans une LIST Redis cappée (`LTRIM`).
- Justification : un message de chat a une valeur à très courte durée.
  Persister tous les messages d'une plateforme de streaming coûte cher et
  apporte peu (les conversations sont éphémères, contextuelles au stream).
- Si on a besoin d'analytics ou de modération a posteriori plus tard, on
  ajoutera un consommateur qui dump dans un store froid (S3 + bigquery).

### Modération
- **`ChatBan` en DB** : c'est durable, donc DB (vs. messages → Redis).
- Commandes streamer : `/timeout <user> <min>`, `/ban <user>`, `/unban <user>`,
  `/slowmode <s>` (0 = off).
- Vérifications côté serveur uniquement (jamais confiance client).
- Slow-mode stocké en Redis (`chat:slowmode:<channel_id>`).

### Anti-spam
- Rate-limit perso 1 msg / 1.5 s minimum (Redis `SET NX PX`).
- Si slow-mode actif, on prend le max(slow, 1.5).
- Validation : 500 chars max, strip, pas vide.

### Viewers count
- Compteur Redis `chat:viewers:<channel_id>`, `INCR` à la connexion,
  `DECR` à la déconnexion, TTL 1h pour auto-nettoyage en cas de crash
  conn non fermées.
- Exposé dans `/api/channels/<slug>/status` (déjà cacheable 5s).

## Conséquences

### Positives
- Architecture **simple** : un consumer, une LIST Redis, une table de bans.
- **Scaling vertical** confortable : Daphne + Redis tiennent facilement
  10 000+ connexions WS par instance sur un Droplet 2 vCPU.
- **Modération efficace** : kick instantané via group message, ban
  persistant en DB.
- **Pas de fuite mémoire** : Redis LIST cappée par `LTRIM`, compteur
  viewers avec TTL.

### Négatives / dette
- **Pas d'historique long** : si quelqu'un arrive 30 min après le début
  du stream, il ne voit que les 100 derniers messages. Acceptable.
- **JWT en query param** : risque résiduel de fuite log. Mitigé par TTL
  court + filter nginx.
- **Bans non-fédérés** : un user banni d'une chaîne reste libre ailleurs.
  C'est voulu (chaque streamer modère son chat).

## Alternatives écartées

- **Tous les messages en DB Postgres** : coût IO + index à maintenir,
  pour des données quasi sans valeur après quelques minutes.
- **Sockets natifs / engine.io** : Channels suffit largement au MVP, et
  reste dans l'écosystème Django.
- **Auth WS via cookie** : possible mais Safari WS avec cookies
  cross-origin a des subtilités, et le query param est plus universel.

## Révision

À revoir si :
- Besoin d'historique persistant pour analytics ou compliance.
- Plus de 50 000 connexions concurrentes par instance Daphne → sharder
  par channel layer ou passer à NATS/Redis Cluster.
- Apparition d'attaques DDoS sur les WS → ajouter un layer Cloudflare WS
  ou un rate-limit par IP au handshake.
