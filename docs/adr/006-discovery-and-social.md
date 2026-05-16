# ADR 006 — Découverte et social (follows + catalogue)

- **Statut** : Acceptée
- **Date** : 2026-05-16

## Contexte

Phase 5 ajoute la couche social et découverte : follows, page d'accueil
trillée par viewers, catégories de jeux, recherche basique. On veut un
MVP fonctionnel sans empiler de stack complexe (Elasticsearch,
notification platform, etc.).

## Décision

### Follows
- Modèle `social.Follow(follower → followee)`. **Target = User**, pas
  Channel : au MVP `User` ↔ `Channel` est 1-1 et ça reste compatible si
  un user a plusieurs chaînes plus tard (on continuera à suivre la
  personne, pas un slot technique).
- Endpoints : `POST/DELETE /api/follows/<username>`,
  `GET /api/follows/<username>/status`, `GET /api/follows/me`.
- Idempotents (POST 2× = OK), self-follow refusé.

### Catalogue
- App `catalog` avec un modèle `Game(slug, name, box_art_url)`.
- Curation manuelle au MVP, seed de 10 jeux populaires
  (`catalog/fixtures/games_seed.json`).
- `Channel` gagne un FK nullable vers `Game` (catégorie courante du
  stream).

### Découverte
- `GET /api/discover/live` : tous les `is_live=True`, viewers count via
  `MGET` Redis (cf. ADR 005), tri viewers desc, pagination limit/offset.
- `GET /api/discover/categories` : tri par `live_count` desc via
  `annotate(Count, filter=Q(is_live=True))`.
- `GET /api/discover/categories/<slug>` : lives sur ce jeu, même format
  que `/discover/live`.
- `GET /api/discover/search?q=...` : recherche Postgres `icontains` sur
  `Channel.slug`, `User.display_name`, `Game.name`. Limite 20. q < 2
  caractères → réponse vide (pas de fishing accidentel).

### Notifications follower-live-started
- **Reporté**. La tâche Celery existe (`notify_followers_live_started`)
  mais se contente de logger les IDs concernés.
- Justification : on attend d'avoir des followers réels avant d'investir
  dans un canal de notification (email, push web, mobile). Le code
  d'orchestration est en place, il suffit d'ajouter un sender.

## Conséquences

### Positives
- **Pas de stack search** (Elasticsearch / Meilisearch) au MVP. `icontains`
  Postgres tient jusqu'à quelques milliers de chaînes sans souci.
- **Catalogue maîtrisé** : on évite le user-generated tagging anarchique
  des débuts (le streamer choisit dans une liste finie).
- **Follow découplé** : pas besoin de re-toucher cette table quand on
  ajoutera des features de notification.
- Tri viewers via `MGET` Redis : 1 round-trip réseau, suffit largement.

### Négatives / dette
- **Recherche limitée** : pas de tolérance aux fautes, pas de boost,
  pas de personnalisation. À refactor quand on aura > 1k chaînes
  actives ou des plaintes utilisateur.
- **Catalogue curaté** : implique du travail manuel pour ajouter un jeu.
  Acceptable, mais on ajoutera un workflow "demande d'ajout" si besoin.
- **Pas de cache HTTP** sur `/discover/*` pour l'instant : la donnée
  bouge à la minute. À cacher Cloudflare 10-30 s plus tard si charge.

## Alternatives écartées

- **Follow Channel-target** : marche, mais ajoute un join. Choix moins
  flexible.
- **Search Elasticsearch / Meilisearch** : énorme over-engineering au
  MVP, ajoute un service à gérer.
- **Tagging libre des catégories** : génère des doublons (`val`,
  `valorant`, `Valorant`, `vlr`) qu'il faut remerger ensuite.
- **Notifs email follower-live immédiates** : coût SMTP non négligeable
  (un streamer populaire avec 1k followers = 1k emails à chaque go-live),
  et bénéfice incertain au MVP.

## Révision

À revoir quand :
- > 10 000 chaînes : envisager Postgres trigram + GIN, ou un vrai search.
- Demande croissante de tagging : workflow d'ajout de jeu via dashboard
  admin léger.
- Acquisition utilisateur active : prioriser les notifs follower-live
  (push web d'abord, mail en backup).
