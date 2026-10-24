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

## Health & status

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `GET` | `/api/livez` | — | Liveness simple (process up). Aucune dépendance. |
| `GET` | `/api/healthz` | — | Ping DB + Redis. `200 {status, db, redis}` ou `503 {degraded,…}`. |
| `GET` | `/api/status` | — | État détaillé pour la page publique `/statut` : `services: {api, database, redis, bunny_stream}` avec `{ok, latency_ms}` chacun, `checked_at`, `uptime_pct_30d`, `incidents`. |

---

## Charity Day — `/api/charity/`

Module RSE : 1 événement caritatif par mois, dons en Aura, transparence totale.
Les commissions plateforme sont prélevées sur les flux Tips/Subs (cf. monétisation) ;
les dons Charity Day passent du wallet utilisateur vers la cause via un ledger
dédié (`LedgerEntry.Kind.CHARITY_DONATION`).

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `GET` | `/api/charity/events` | — | Liste publiée des Charity Days (récents + à venir). |
| `GET` | `/api/charity/events/current` | — | Événement en cours (sinon le prochain) avec totaux + leaderboard. |
| `GET` | `/api/charity/events/<slug>` | — | Détail + agrégats : `total`, `donor_count`, `by_charity`, `top_donors`. |
| `GET` | `/api/charity/charities` | — | Catalogue des associations agréées. |
| `POST` | `/api/charity/donate` | JWT, 5/min | `{event_slug, charity_slug, aura_amount, message?, anonymous?}`. Atomique : débit wallet + création donation + maj cache total. Refus si < floor, hors fenêtre, asso non bénéficiaire. |

## Calendrier d'événements — `/api/events/`

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `GET` | `/api/events` | — | Liste publique, filtrable par `kind` (`charity\|tournament\|premiere\|announcement\|maintenance`) et `from`/`to` ISO. |
| `GET` | `/api/events/upcoming?limit=5` | — | N prochains événements (header menu). |
| `GET` | `/api/events/<slug>` | — | Détail d'un événement. |

Les `CharityEvent` sont automatiquement miroir dans `PlatformEvent` (signal).

## Annonces — `/api/announcements/`

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `GET` | `/api/announcements/active` | optionnel (filtre audience) | Annonces actives selon `audience` (anonymous/viewers/streamers/all) : `{results:[{id, title, body, level, display_mode, dismissible, cta_label, cta_url}]}`. |

---

## Authentification & comptes — `/api/auth/`

| Méthode | Chemin | Auth | Rate-limit | Description |
|---------|--------|------|-----------|-------------|
| `POST` | `/api/auth/register` | — | 5 / 5 min / IP | Crée un compte `{email, username, password, password_confirm, date_of_birth (AAAA-MM-JJ), invite?, terms_accepted}`. **18 ans minimum** (vérifié sur `date_of_birth`), mot de passe ≥ 8 caractères (non similaire à l'email/pseudo, non courant), confirmation identique, `terms_accepted=true`. Erreurs : `{detail: <premier message>, errors: {champ: [...]}}`. |
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
| `GET` | `/api/channels/me` | JWT | — | Ma chaîne, **avec identifiants de stream** (`ingest_url`, `stream_key`, si provisionnée) + `follower_count`, `viewers`. |
| `PATCH` | `/api/channels/me` | JWT | — | Met à jour `{title?, thumbnail_url?, banner_url?, social_links?, category_slug?, goal_title?, goal_kind?, goal_target?}` (changer l'objectif remet sa progression à zéro). `social_links` : clés ∈ {twitter, youtube, instagram, tiktok, discord, website}. |
| `GET` | `/api/channels/me/sessions` | JWT | `limit` (≤100, déf 50) | Historique des diffusions : `started_at`, `ended_at`, `duration_seconds`, `peak_viewers`, `category`. |
| `POST` | `/api/channels/me/key/rotate` | JWT | 5 / j / user | Régénère la clé de stream. **403** si chaîne non provisionnée. |
| `GET` | `/api/channels/<slug>` | — | — | Chaîne publique (sans secrets) : streamer (+ bio), bannière, réseaux sociaux, catégorie, HLS, statut. |
| `GET` | `/api/channels/<slug>/status` | — | cache 5 s | `{is_live, last_live_started_at, viewers}` (poll du badge LIVE). |

| `POST` | `/api/channels/me/live` | JWT | 60 / h / user | Bascule live manuelle (repli du polling). **403** si chaîne non provisionnée. |
| `GET` | `/api/overlay/<token>` | jeton overlay | 120 / min / IP | Données des widgets OBS : `{slug, is_live, goal: {title, kind: subs\|tips, target, current} \| null}`. |
| `GET` | `/api/channels/me/stream-health` | JWT | 30 / min | État du flux côté Bunny (`provider`, `mode`, `is_live`, `reachable`, `checked_at`). **403** si non provisionnée. |

> ⚠️ `stream_key` n'est **jamais** exposée dans la vue publique, uniquement
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
validation admin (panel) → provisioning Bunny Stream à l'approbation. Quota
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
par défaut, **Stripe** si clé, **mobile money** à brancher). Toutes les mutations
passent par un grand livre (`LedgerEntry`) atomique.

**Business model** (commissions plateforme, prélèvement *unique* par flux pour
éviter le double prélèvement du streamer) :

| Flux | Commission | Sur qui ? | Quand |
|------|------------|-----------|-------|
| **Tip** | 30 % | Sur le créateur (split à la réception) | À chaque tip (min. `TIP_MIN_AURA` = 10) |
| **Abonnement** | 30 % | Sur le créateur (split au prélèvement) | À chaque période payée (prix verrouillé) |
| **Achat d'Aura** | 1 % | **Streamer uniquement** (viewer = 0 %) | À la confirmation de l'achat |
| **Retrait** | 3 % (frais de traitement) | Sur le montant retiré | Comptabilisé quand le retrait est **payé** |

Les taux sont stockés dans `FeeRule` (**une seule règle active par produit**,
admin-éditables) et seedés au déploiement (migration `payments/0008_seed_default_fees`).
Chaque commission est tracée dans **`PlatformRevenue`** (même transaction que le flux).

**Règles de sécurité** :
- seule l'Aura **gagnée** (tips + abonnements reçus) est retirable ; l'Aura achetée
  ou offerte (parrainage) ne se convertit jamais en argent ;
- seules les chaînes **approuvées** (provisionnées) reçoivent tips et abonnements ;
- providers **simulés** (fake, Wave/Orange Money sans clé) refusés hors dev, sauf
  `PAYMENTS_ALLOW_FAKE=1` (démo assumée) ;
- clés `Idempotency-Key` scopées **par utilisateur** (achat, tip, abonnement) ;
- remboursement / litige Stripe → reprise de l'Aura ; si déjà dépensée, gel des
  retraits (`Wallet.payout_hold`) + `RiskEvent` « chargeback » ;
- `python manage.py reconcile_wallets` vérifie solde = somme du ledger.

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `GET` | `/api/payments/wallet` | JWT | `{aura_balance, unit_price_xof, payout_hold, recent:[ledger…]}`. |
| `POST` | `/api/payments/purchase` | JWT | `{credits, method}` → achat. Simulé = crédité tout de suite ; Stripe → `{checkout_url}`. |
| `GET` | `/api/payments/purchases/<id>` | JWT | Statut d'un achat (suivi du retour Stripe `?paid=1&purchase=<id>`). |
| `POST` | `/api/payments/tip` | JWT | `{channel_slug, aura_amount, message?}` → débit envoyeur, crédit créateur (70 %). |
| `GET` | `/api/payments/withdrawal/eligibility` | JWT | `{is_streamer, withdrawable, fee_pct, min_aura, payout_hold}`. |
| `POST` | `/api/payments/withdrawal/quote` | JWT | `{aura_amount}` → `{fee_aura, net_aura, net_fiat}` (calcul identique au retrait réel). |
| `POST` | `/api/payments/withdrawal/start` | JWT | `{aura_amount, destination_provider: wave\|orange_money, destination_phone}` → OTP par **e-mail**. |
| `POST` | `/api/payments/withdrawal/confirm` | JWT | `{code}` → crée le `Payout` (Aura brute mise en réserve). |
| `GET` | `/api/payments/payouts` | JWT | Historique de mes retraits. |
| `POST` | `/api/payments/webhook/<provider>` | signature provider | `paid` → crédit (une seule fois), `refunded`/`disputed` → reprise. **404** si provider inconnu. |
| `POST` | `/api/admin/payouts/<id>/resolve` | admin | `{action: processing\|paid\|fail}` ; `fail` recrédite (`payout_reversal`). |

> L'ancien `POST /api/payments/payout` (retrait sans contrôle) est **supprimé**.

Réglages : `AURA_UNIT_PRICE_XOF`, `EUR_XOF_RATE`, `USD_XOF_RATE`, `CREATOR_SHARE`, `PAYMENTS_PROVIDER`,
`PAYMENTS_ALLOW_FAKE`, `WITHDRAWAL_PROCESSING_FEE_PCT`, `WITHDRAWAL_MIN_AURA`, `TIP_MIN_AURA`,
`SUB_TIER_MAX_AURA`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`.

**Abonnements** : le prix est **verrouillé** à la souscription (`price_paid`) ; un
réabonnement prolonge la période en cours ; l'annulation coupe le renouvellement
mais garde l'accès jusqu'à la fin du mois payé (`POST …/resume` pour réactiver) ;
un abonnement offert ne se renouvelle pas.

---

## Instant (vidéos courtes) — `/api/shorts/`

Vidéos verticales ≤ 60 s publiées par les streamers approuvés, hébergées sur
**Bunny Stream** (VOD). Upload **direct navigateur → Bunny** (TUS signé), puis le
webhook Bunny (`/api/webhooks/bunny/stream`, statut 3 = prête, 5 = échec) publie
la vidéo. En mode FAKE, la vidéo est publiée tout de suite avec un clip de démo.

| Méthode | Chemin | Auth | Description |
|---------|--------|------|-------------|
| `GET` | `/api/shorts/trending?limit&offset` | — | Fil public classé par popularité amortie par l'âge (`(vues + 5·likes + 1) / (âge_h + 2)^1.5`), suivis ou non. `liked` si connecté. |
| `GET` | `/api/shorts/<id>` | — | Détail d'une vidéo visible. |
| `POST` | `/api/shorts/<id>/view` | — (240/h/IP) | +1 vue, dédoublonnée 6 h par spectateur (Redis). |
| `POST`/`DELETE` | `/api/shorts/<id>/like` | JWT | Aimer / ne plus aimer (idempotent) → `{liked, like_count}`. |
| `GET` | `/api/channels/<slug>/shorts` | — | Vidéos Instant d'une chaîne. |
| `GET`/`POST` | `/api/shorts/me` | JWT streamer | Mes vidéos (tous statuts) / démarrer un upload `{title}` → `{short, upload: {mode: "tus", endpoint, library_id, video_id, expires, signature} \| {mode: "fake"}}`. Max 5 envois en cours. |
| `POST` | `/api/shorts/me/<id>/uploaded` | JWT | Fin de l'envoi TUS → statut « encodage ». |
| `DELETE` | `/api/shorts/me/<id>` | JWT | Supprime la vidéo (et le fichier Bunny). |

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
| `POST` | `/api/webhooks/bunny/stream` | HMAC-SHA256 | Événements Bunny Stream : statut d'encodage des vidéos « Instant » (`VideoGuid`, `Status` 3 = prête, 5 = échec) ; événements live éventuels (`LiveStreamId`, `State`) → bascule `is_live`. |

**Signature** : en-tête `X-BunnyStream-Signature` = HMAC-SHA256 hex du corps
brut, clé `BUNNY_STREAM_WEBHOOK_KEY`. L'état live est par ailleurs synchronisé
par polling (Celery beat `sync_live_status`, cf. [ADR 010](adr/010-bunny-stream.md)).

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
└── webhooks/bunny/stream            POST

WebSocket
└── ws/c/<slug>/chat                 (?token=<JWT>)
```

> **Schéma complet & à jour** : OpenAPI auto-généré sur **`/api/schema`**
> (Swagger UI : **`/api/docs`**). La liste ci-dessous résume les ajouts v2.

### Routes v2 (résumé)

```
/api/
├── auth/register                    POST  (+ `password_confirm`, `date_of_birth` 18+, `terms_accepted`, `invite` optionnel)
├── uploads/{avatar,banner,game/<slug>}      POST  (multipart → Cloudflare R2)
├── payments/
│   ├── wallet · purchase · purchases/<id> · tip · payouts
│   ├── withdrawal/{eligibility,quote,start,confirm}
│   └── history                      GET   (ledger paginé)
├── channels/<slug>/tier             GET   (palier public)
├── streamer/tier                    GET, PUT
├── subscriptions                    POST
├── subscriptions/me                 GET   (mes abonnements actifs)
├── subscriptions/gift               POST  (offrir un abo : `{channel_slug, recipient}`)
├── subscriptions/gifted             GET   (abos que j'ai offerts)
├── subscriptions/<slug>/status      GET
├── subscriptions/<slug>/resume      POST  (réactive le renouvellement)
├── subscriptions/<slug>             DELETE (annule le renouvellement, accès conservé)
├── analytics/me/revenue             GET   (revenus créateur jour/semaine/mois)
├── achievements                     GET   (mon catalogue + débloqués, champs name/criteria/icon/icon_url)
├── achievements/<username>          GET   (public — succès débloqués d'un profil + total)
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

## Routes v4 (dashboard, gamification, sécurité)

### Comptes et sécurité — `/api/auth/`

| Méthode | Route | Rôle |
|---|---|---|
| POST | `/api/auth/password/change` | Nouveau mot de passe (`password` actuel requis) ; déconnecte les autres appareils. |
| GET / POST | `/api/auth/2fa/recovery-codes` | Codes de secours restants / nouveaux codes (`password` + `code`). |
| POST | `/api/auth/2fa/disable` | Désactive la 2FA : `password` **et** `code` requis. |
| GET | `/api/auth/passkeys` | Passkeys du compte. |
| POST | `/api/auth/passkeys/register/options` | Options WebAuthn d'enregistrement (`password` requis). |
| POST | `/api/auth/passkeys/register/verify` | `{credential, name}` → passkey créée. |
| PATCH / DELETE | `/api/auth/passkeys/<id>` | Renommer (`name`) / supprimer (`password`). |
| POST | `/api/auth/passkeys/login/options` | `{handle, options}` (défi 5 min, usage unique). |
| POST | `/api/auth/passkeys/login/verify` | `{handle, credential}` → session (access + cookie). |

Limites : 5 échecs de connexion par compte → 429 pendant 15 min (en plus de la
limite par IP). Le lien de réinitialisation ne sert qu'une fois. Les retraits
exigent `totp` en plus du code e-mail quand la 2FA est active.

### Profil, niveaux et badges

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/users/<username>/profile` | Profil public : niveau, chaînes soutenues (badge de don), succès, compteurs. Montants visibles par le seul propriétaire. |
| GET | `/api/users/me/level` | `{level, next_level, next_at, progress, spent}`. |

Les messages du chat portent `user.level` (niveau, Aura dépensée à vie) et
`user.gift_tier` (badge de don pour cette chaîne).

### Dashboard streamer — `/api/channels/me/…`

| Méthode | Route | Rôle |
|---|---|---|
| GET / PATCH | `/api/channels/me/chat-settings` | Followers / abonnés seulement, âge du compte, emotes seulement, mode lent, nombre de spectateurs, `automod` (catégories 0–3, `gibberish`, `spam`). |
| GET / POST | `/api/channels/me/banned-words` | Mots interdits de la chaîne. |
| DELETE | `/api/channels/me/banned-words/<id>` | Retirer un mot. |
| GET | `/api/channels/me/mod-actions` | Journal de modération (bans, timeouts, suppressions, automod, réglages). |
| GET | `/api/channels/me/unban-requests?status=` | Demandes de déban. |
| POST | `/api/channels/me/unban-requests/<id>/decide` | `{decision: approve\|deny}`. |
| GET | `/api/channels/me/followers`, `/api/channels/me/subscribers` | Listes paginées (`limit`, `offset`). |
| GET / POST | `/api/c/<slug>/unban-request` | Spectateur banni : état / demande (`message`). |

`/api/channels/me` (GET, PATCH, rotation de clé) renvoie aussi `follower_count`,
`viewers` et `active_subs`. Le fil `/api/channels/me/activity` distingue
`subscribe`, `resub` et `gift`.

### Divers

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/api/media/<path>` | Images stockées localement quand R2 n'est pas configuré. |
| GET | `/api/notifications?before=<id>&limit=` | Pagination par curseur (`next_before`). |
| POST | `/api/notifications/read` | `{ids}` ou `{except: ["support_message"]}` → `{marked, unread}`. |

## Stockage Redis (éphémère)

| Clé | Type | Rôle |
|-----|------|------|
| `chat:msgs:{channel_id}` | List (cap 100) | Historique chat |
| `chat:viewers:{channel_id}` | Int (TTL 1 h) | Viewers actifs |
| `chat:slowmode:{channel_id}` | Int | Délai slow-mode |
| `chatrl:{channel_id}:{user_id}` | String (TTL) | Sentinelle rate-limit |
