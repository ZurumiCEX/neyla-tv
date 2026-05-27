# Référence API — Neyla TV

API REST (Django REST Framework) + WebSocket (Channels). Toutes les routes
HTTP sont préfixées par `/api/`. L'admin Django est servi sous `/admin/`.

## Conventions

- **Format** : JSON. `Content-Type: application/json`.
- **Auth** : JWT `Bearer` dans l'en-tête `Authorization` pour les routes
  protégées. Le *refresh token* vit dans un cookie HttpOnly (`neyla_refresh`).
  → [ADR 002](adr/002-jwt-strategy.md)
- **Codes** : `200/201` succès, `204` succès sans corps, `400` validation,
  `401` non authentifié, `403` interdit, `404` introuvable, `429` rate-limit,
  `503` dépendance down (health).
- **Rate-limit** : certains endpoints sont limités (par IP ou par utilisateur),
  indiqué dans les tables ci-dessous. Dépassement → `429`.

---

## Health

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `GET` | `/api/healthz` | — | Ping DB + Redis. `200 {status:"ok",db,redis}` si tout est up, sinon `503 {status:"degraded",...}`. |

---

## Authentification & comptes — `/api/auth/`

| Méthode | Chemin | Auth | Rate-limit | Description |
|---------|--------|------|-----------|-------------|
| `POST` | `/api/auth/register` | — | 5 / 5 min / IP | Crée un compte `{email, username, password}`. |
| `POST` | `/api/auth/login` | — | 10 / 5 min / IP | `{email, password}` → `{access, user}` + cookie refresh. |
| `POST` | `/api/auth/refresh` | cookie | — | Rafraîchit l'access token depuis le cookie (ou `{refresh}`). |
| `POST` | `/api/auth/logout` | cookie | — | Blackliste le refresh, efface le cookie. `204`. |
| `GET` | `/api/auth/me` | JWT | — | Profil de l'utilisateur courant. |
| `PATCH` | `/api/auth/me` | JWT | — | Met à jour `{display_name?, avatar_url?, bio?}`. |
| `POST` | `/api/auth/email/verify` | — | — | Vérifie l'email via `{token}`. |
| `POST` | `/api/auth/email/resend` | JWT | 3 / h / user | Renvoie l'email de vérification. |
| `POST` | `/api/auth/password/reset/request` | — | 5 / h / IP | Demande un reset `{email}` (réponse générique). |
| `POST` | `/api/auth/password/reset/confirm` | — | 10 / h / IP | Confirme via `{token, password}`. |

**Objet `User`** : `id, email, username, display_name, avatar_url, bio,
is_email_verified, date_joined`.

---

## Chaînes — `/api/channels/`

| Méthode | Chemin | Auth | Rate-limit | Description |
|---------|--------|------|-----------|-------------|
| `GET` | `/api/channels/me` | JWT | — | Ma chaîne, **avec credentials RTMPS** (si provisionnée) + `follower_count`, `viewers`. |
| `PATCH` | `/api/channels/me` | JWT | — | Met à jour `{title?, thumbnail_url?, banner_url?, social_links?, category_slug?}`. `social_links` : clés ∈ {twitter, youtube, instagram, tiktok, discord, website}. |
| `GET` | `/api/channels/me/sessions` | JWT | `limit` (≤100, déf 50) | Historique des diffusions : `started_at`, `ended_at`, `duration_seconds`, `peak_viewers`, `category`. |
| `POST` | `/api/channels/me/key/rotate` | JWT | 5 / j / user | Régénère la clé de stream. **403** si chaîne non provisionnée. |
| `GET` | `/api/channels/<slug>` | — | — | Chaîne publique (sans secrets) : streamer (+ bio), bannière, réseaux sociaux, catégorie, HLS, statut. |
| `GET` | `/api/channels/<slug>/status` | — | cache 5 s | `{is_live, last_live_started_at, viewers}` (poll du badge LIVE). |

> ⚠️ `rtmps_key` n'est **jamais** exposée dans la vue publique, uniquement
> dans `/api/channels/me`.

---

## Découverte & catégories — `/api/discover/`

| Méthode | Chemin | Auth | Query | Description |
|---------|--------|------|-------|-------------|
| `GET` | `/api/discover/live` | — | `limit` (≤100, déf 20), `offset` | Lives en cours (avec viewers). |
| `GET` | `/api/discover/categories` | — | `limit`, `offset` | Catégories (jeux) + nombre de lives. |
| `GET` | `/api/discover/categories/<slug>` | — | `limit`, `offset` | Une catégorie + ses lives. |
| `GET` | `/api/discover/search` | — | `q` (≥2 car., requis) | Recherche `{channels, games}`. |

---

## Social (follow) — `/api/follows/`

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `GET` | `/api/follows/me` | JWT | Chaînes suivies (triées par date desc). |
| `POST` | `/api/follows/<username>` | JWT | Suivre. `201 {following:true}`. |
| `DELETE` | `/api/follows/<username>` | JWT | Ne plus suivre. `204`. |
| `GET` | `/api/follows/<username>/status` | JWT | `{following: bool}`. |

---

## Streamer (candidature) — `/api/streamer/`

L'inscription est ouverte à tous, mais **streamer est gaté** : candidature →
validation admin (panel) → provisioning Cloudflare à l'approbation. Quota
quotidien d'approbations configurable (`STREAMER_DAILY_APPROVAL_QUOTA`, défaut 100).

| Méthode | Chemin | Auth | Rate-limit | Description |
|---------|--------|------|-----------|-------------|
| `POST` | `/api/streamer/apply` | JWT | 3/h/user | Dépose/réessaie une candidature `{motivation?}`. `201` → application. `409` si déjà streamer. |
| `GET` | `/api/streamer/application` | JWT | — | Statut courant : `{status: none\|pending\|approved\|rejected, ...}`. |

L'approbation/rejet se fait dans l'admin Django (actions « Approuver » / « Rejeter »
sur `StreamerApplication`). L'approbation provisionne la chaîne via la task
`provision_live_input_task` (réutilisée).

---

## Chat — REST + WebSocket

### Historique (REST)

| Méthode | Chemin | Auth | Query | Description |
|---------|--------|------|-------|-------------|
| `GET` | `/api/c/<slug>/chat/history` | — | `limit` (≤100) | Derniers messages `{messages:[...]}`. |

### Live chat (WebSocket)

```
ws(s)://<host>/ws/c/<slug>/chat?token=<JWT_access>
```

- **Auth** : JWT passé en query param `?token=` (cf. [ADR 005](adr/005-chat-architecture.md)).
  Sans token → connecté en anonyme (lecture seule selon les règles).
- **Connexion autorisée** si la chaîne est `is_live` **ou** si l'utilisateur
  est le streamer. Un ban actif ferme la connexion (`4403`).

**Client → serveur**
```json
{ "content": "mon message (≤500 car.)" }
```
Commandes streamer (envoyées comme un message) :
`/slowmode <s>` · `/ban @user` · `/timeout @user [min]` · `/unban @user`

**Serveur → client**
```json
{ "type": "message", "msg": { "id", "user": {"username","display_name"}, "content", "ts" } }
{ "type": "system",  "detail": "Slow-mode → 5s" }
{ "type": "error",   "detail": "Tu vas trop vite." }
{ "type": "kicked",  "detail": "raison" }
```

---

## Webhooks

| Méthode | Chemin | Sécurité | Description |
|---------|--------|----------|-------------|
| `POST` | `/api/webhooks/cloudflare/stream` | HMAC-SHA256 | Événements Cloudflare Stream (`live_input.connected/disconnected`) → bascule `is_live`. |

**Signature** : en-tête `Webhook-Signature: time=<unix>,sig1=<hmac_sha256>`,
vérifiée avec `CLOUDFLARE_WEBHOOK_SECRET`. Tolérance de fraîcheur
`WEBHOOK_TIMESTAMP_TOLERANCE_SECONDS` (300 s par défaut) → anti-rejeu.

---

## Récapitulatif des routes

```
/api/
├── healthz                          GET
├── auth/
│   ├── register · login · refresh · logout
│   ├── me                           GET, PATCH
│   ├── email/verify · email/resend
│   └── password/reset/{request,confirm}
├── channels/
│   ├── me                           GET, PATCH
│   ├── me/key/rotate                POST
│   ├── <slug>                       GET
│   └── <slug>/status                GET
├── discover/{live,categories,categories/<slug>,search}   GET
├── follows/{me,<username>,<username>/status}
├── c/<slug>/chat/history            GET
└── webhooks/cloudflare/stream       POST

WebSocket
└── ws/c/<slug>/chat                 (?token=<JWT>)
```

## Stockage Redis (éphémère)

| Clé | Type | Rôle |
|-----|------|------|
| `chat:msgs:{channel_id}` | List (cap 100) | Historique chat |
| `chat:viewers:{channel_id}` | Int (TTL 1 h) | Viewers actifs |
| `chat:slowmode:{channel_id}` | Int | Délai slow-mode |
| `chatrl:{channel_id}:{user_id}` | String (TTL) | Sentinelle rate-limit |
