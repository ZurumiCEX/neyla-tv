# Référence API — Neyla TV

API REST (Django REST Framework) + WebSocket (Channels). Toutes les routes
HTTP sont préfixées par `/api/`. L'admin Django est servi sous `/admin/`.

> **OpenAPI** : schéma sur `GET /api/schema`, Swagger UI sur `GET /api/docs`
> (drf-spectacular). Pagination DRF (`page`/`page_size`) + filtres/tri/recherche
> (django-filter) sur les vues qui les déclarent. Erreurs au format
> `{detail, errors?}`. Actions sensibles tracées dans `audit.AuditEvent`.

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
| `POST` | `/api/auth/register` | — | 5 / 5 min / IP | Crée un compte `{email, username, password, invite?, terms_accepted}`. `terms_accepted=true` est **obligatoire** (attestation 13 ans + CGU). |
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

**Creator Application System** : la candidature est un formulaire détaillé
(identité, profil gaming, motivation/vision, expérience, équipement, signaux
forts) ; un **score automatique** (0–100) aide l'admin à prioriser.

| Méthode | Chemin | Auth | Rate-limit | Description |
|---------|--------|------|-----------|-------------|
| `POST` | `/api/streamer/apply` | JWT | 3/h/user | Dépose/réessaie une candidature détaillée. `rules_accepted=true` **obligatoire**. Calcule le `score`. `201` → application. `400` si règles non acceptées. `409` si déjà streamer. |
| `GET` | `/api/streamer/application` | JWT | — | Statut + champs : `{status: none\|pending\|under_review\|interview\|approved\|rejected, score, ...}`. |

Payload `apply` (tous optionnels sauf `rules_accepted`) : `full_name, country,
primary_language, main_games, content_categories[], motivation, goals[],
community_type[], has_streamed, platforms{twitch,youtube,tiktok,kick,facebook,
discord}, community_size, frequency, avg_duration, setup[], connection_quality,
why_select, what_bring, intro_video_url, setup_screenshot_url, rules_accepted`.

**Scoring** (max 100) : expérience streaming +20, communauté existante +25,
qualité de motivation +20, fréquence +15, setup +10, réseaux actifs +10.

L'approbation/rejet/mise en examen/entretien se font dans l'admin Django
(actions sur `StreamerApplication` : Approuver, Rejeter, « en cours d'examen »,
« Demander un entretien » ; tri par score, filtres, notes & tags). L'approbation
**provisionne la chaîne de façon synchrone** (aucune dépendance au worker Celery).

---

## Guides & tutoriels — `/api/guides`

Le **contenu** des guides est géré en base (back-office Django : modèles
`Guide` + `GuideStep`, CRUD, localisation FR/EN/PT, publication/ordre). La
**progression** est par utilisateur, clé `"<slug>:<step_id>"`.

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `GET` | `/api/guides?locale=fr\|en\|pt` | — | Guides publiés + étapes, localisés : `{results:[{slug, icon, title, desc, steps:[{id,title,body}]}]}`. |
| `GET` | `/api/guides/progress` | JWT | Clés d'étapes validées : `{completed:[...]}`. |
| `POST` | `/api/guides/progress` | JWT | `{key, done?}` (dé)valide une étape. |

Le front consomme `/api/guides` (repli sur le contenu intégré si l'API est
vide/indisponible). Les `slug`/`step_id` sont stables (clé de progression).

---

## Notifications — `/api/notifications`

Notifications in-app créées **de façon synchrone** : live d'une chaîne suivie,
nouveau follower, décision de candidature streamer.

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `GET` | `/api/notifications` | JWT | `{results: [{id, type, payload, read_at, created_at}], unread: int}` (50 plus récentes). |
| `POST` | `/api/notifications/read` | JWT | Marque lu. Corps `{ids?: [int]}` (sinon **tout** marquer lu). `{marked: int}`. |

Types : `live_started` (payload `{slug, display_name}`), `new_follower`
(`{username}`), `application_decided` (`{status, reason}`).

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
`/slowmode <s>` · `/ban @user` · `/timeout @user [min]` · `/unban @user` ·
`/delete <message_id>`

Les messages contenant un **mot interdit** (table `moderation.BannedWord`,
chargée à la connexion) sont bloqués (`{type:"error"}`).

**Serveur → client**
```json
{ "type": "message", "msg": { "id", "user": {"username","display_name"}, "content", "ts" } }
{ "type": "delete",  "id": "<message_id>" }
{ "type": "system",  "detail": "Slow-mode → 5s" }
{ "type": "error",   "detail": "Tu vas trop vite." }
{ "type": "kicked",  "detail": "raison" }
```

---

## Modération — `/api/reports`

| Méthode | Chemin | Auth | Rate-limit | Description |
|---------|--------|------|-----------|-------------|
| `POST` | `/api/reports` | JWT | 20 / h / user | Signale `{reason, target_username?, channel_slug?, message_id?, details?}`. `reason` ∈ {spam, harassment, hate, other}. |

Mots interdits (`BannedWord`) et signalements (`Report`) se gèrent dans l'admin Django.

---

## Analytics — `/api/analytics/`

Calculées **à la demande** (pas de tâche planifiée). DAU/MAU s'appuient sur
`User.last_active_at` (mis à jour à l'appel de `/api/auth/me`).

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `GET` | `/api/analytics/me` | JWT | Résumé streamer : `{sessions_total, broadcast_hours, peak_viewers, follower_count}`. |
| `GET` | `/api/analytics/me/revenue?period=day\|week\|month` | JWT | Revenus consolidés du créateur (tips + abos + parrainage) : `{period, series:[{date,tips,subs,referral,total}], totals, summary:{day,week,month}, withdrawable}`. |
| `GET` | `/api/analytics/overview` | **admin** | Plateforme : `{users_total, dau, mau, streamers_total, live_now, streams_total, streams_7d, broadcast_hours, peak_concurrent, top_streamers:[...]}`. `403` si non-admin. |

---

## Monétisation "Aura" — `/api/payments/`

Crédits "Aura". **Devise = FCFA (XOF)** ; équivalents EUR (parité fixe 655,957) et
USD (taux manuel) renvoyés pour l'affichage. Achat via provider abstrait (**FAKE**
par défaut, **Stripe** si clé, **mobile money** à brancher), tips avec partage
**70 % créateur / 30 % plateforme**, retrait. Toutes les mutations passent par un
grand livre (`LedgerEntry`) atomique.

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `GET` | `/api/payments/wallet` | JWT | `{aura_balance, balance:{xof,eur,usd}, unit_price_xof, recent:[ledger…]}`. |
| `POST` | `/api/payments/purchase` | JWT | `{credits}` → achat. FAKE = crédité tout de suite ; Stripe → `{checkout_url}`. |
| `POST` | `/api/payments/tip` | JWT | `{channel_slug, aura_amount, message?}` → débit envoyeur, crédit créateur (70 %). |
| `POST` | `/api/payments/payout` | JWT | `{aura_amount}` → demande de retrait (débit + `Payout`). |
| `POST` | `/api/payments/webhook/<provider>` | signature provider | Confirme un achat (idempotent) → crédite le wallet. |

Réglages : `AURA_UNIT_PRICE_XOF`, `EUR_XOF_RATE`, `USD_XOF_RATE`, `CREATOR_SHARE`, `PAYMENTS_PROVIDER`,
`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`.

---

## Uploads médias — `/api/uploads/`

Multipart (`file`), PNG/JPEG/WebP, ≤ 5 Mo. Stockage **Cloudflare R2** (mode FAKE
si non configuré → URL `fake.local`).

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `POST` | `/api/uploads/avatar` | JWT | Upload + set `avatar_url`. → `{url}`. |
| `POST` | `/api/uploads/banner` | JWT | Upload + set `Channel.banner_url`. → `{url}`. |
| `POST` | `/api/uploads/game/<slug>` | **admin** | Upload + set `Game.box_art_url`. → `{url}`. |

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

> **Schéma complet & à jour** : OpenAPI auto-généré sur **`/api/schema`**
> (Swagger UI : **`/api/docs`**). La liste ci-dessous résume les ajouts v2.

### Routes v2 (résumé)

```
/api/
├── auth/register                    POST  (+ champs `invite` optionnel, `terms_accepted` requis)
├── uploads/{avatar,banner,game/<slug>}      POST  (multipart → Cloudflare R2)
├── payments/
│   ├── wallet · purchase · tip · payout
│   └── history                      GET   (ledger paginé)
├── channels/<slug>/tier             GET   (palier public)
├── streamer/tier                    GET, PUT
├── subscriptions                    POST
├── subscriptions/me                 GET   (mes abonnements actifs)
├── subscriptions/gift               POST  (offrir un abo : `{channel_slug, recipient}`)
├── subscriptions/gifted             GET   (abos que j'ai offerts)
├── subscriptions/<slug>/status      GET
├── subscriptions/<slug>             DELETE
├── analytics/me/revenue             GET   (revenus créateur jour/semaine/mois)
├── achievements                     GET   (catalogue + débloqués)
├── invites                          GET, POST
├── notifications/
│   ├── (list) · read · preferences  GET/PUT
│   └── <id>/read                    POST
├── moderation/reports               GET   (modérateur, filtrable)
├── moderation/reports/<id>          PATCH (statut/résolution/ban)
├── moderation/banned-words/import   POST  (modérateur, texte/CSV)
└── admin/
    ├── dashboard                    GET   (activité + revenus)
    ├── transactions                 GET   (unifiées, filtrables)
    ├── fees · fees/<id>             GET/POST · PATCH/DELETE
    ├── payouts/<id>/resolve         POST  (paid|fail)
    ├── users · users/<id>           GET · PATCH (rôle)
    └── messages                     POST  (support → utilisateur)
```

Permissions par rôle : `IsAdminRole` (hub admin / fees / transactions / users),
`IsModerator` (signalements, mots interdits), `IsSupport` (messagerie).

## Stockage Redis (éphémère)

| Clé | Type | Rôle |
|-----|------|------|
| `chat:msgs:{channel_id}` | List (cap 100) | Historique chat |
| `chat:viewers:{channel_id}` | Int (TTL 1 h) | Viewers actifs |
| `chat:slowmode:{channel_id}` | Int | Délai slow-mode |
| `chatrl:{channel_id}:{user_id}` | String (TTL) | Sentinelle rate-limit |
