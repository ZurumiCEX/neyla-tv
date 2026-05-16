# ADR 002 — Stratégie JWT et stockage du refresh token

- **Statut** : Acceptée
- **Date** : 2026-05-16

## Contexte

Phase 1 de Neyla TV : on doit gérer l'auth côté API (Django + DRF) et côté
navigateur (Next.js). Deux choses à arbitrer :
1. La durée de vie + la rotation des tokens JWT.
2. L'endroit où le navigateur stocke le refresh token.

## Décision

### Durées et rotation

On utilise `djangorestframework-simplejwt` avec :

- `ACCESS_TOKEN_LIFETIME = 15 min`
- `REFRESH_TOKEN_LIFETIME = 7 jours`
- `ROTATE_REFRESH_TOKENS = True` → chaque refresh émet un *nouveau* refresh.
- `BLACKLIST_AFTER_ROTATION = True` → l'ancien est blacklisté immédiatement.
- App `rest_framework_simplejwt.token_blacklist` activée (tables DB pour la blacklist).

Conséquence : un refresh volé n'est utilisable qu'**une seule fois** avant
d'être blacklisté, et l'utilisateur légitime sera déconnecté au prochain
refresh (signal d'alerte).

### Stockage côté navigateur

- **Access token** : retourné dans le **corps JSON** de `/api/auth/login` et
  `/api/auth/refresh`. Le frontend le garde en **mémoire** (React state /
  context). Pas de `localStorage` : court-circuite la classe d'attaques XSS
  → vol persistant. Recharge → on perd l'access et on appelle `/refresh`.
- **Refresh token** : posé par le backend en **cookie HttpOnly**, avec :
  - `HttpOnly` (inaccessible au JS, donc immunisé à XSS direct)
  - `Secure` en prod (HTTPS uniquement)
  - `SameSite=Lax` (bloque l'envoi sur POST cross-site → mitigation CSRF
    suffisante pour un cookie qui n'a qu'un seul endpoint cible)
  - `Path=/api/auth/` (ne fuit pas vers les autres endpoints API)

## Conséquences

### Positives
- XSS direct ne peut pas exfiltrer le refresh.
- `SameSite=Lax` + `Path` restreint + endpoint dédié = surface CSRF nulle
  en pratique (un attaquant ne peut pas déclencher de refresh cross-site).
- Rotation + blacklist → vol de refresh détectable.
- API REST classique côté front : `Authorization: Bearer <access>`.

### Négatives / dette
- Page rechargée = appel `/refresh` systématique au boot du frontend
  (latence supplémentaire ~50 ms). Acceptable.
- Si le frontend et l'API sont sur des domaines différents en prod, il
  faudra `SameSite=None; Secure` et un CORS strict (`Access-Control-Allow-Credentials`).
  À régler en Phase 6.
- Tokens en mémoire = pas de "rester connecté entre onglets" instantané ;
  chaque onglet relance `/refresh` à l'ouverture. Acceptable au MVP.

## Alternatives écartées

- **Refresh en `localStorage`** : plus simple, mais lecture par n'importe
  quel script injecté (XSS). Rejeté.
- **Sessions Django classiques (cookie + CSRF)** : OK pour SSR, mais on
  veut une API utilisable par des clients tiers (mobile plus tard).
- **Access en cookie aussi** : oblige à gérer CSRF sur toutes les routes
  API → trop de friction pour un MVP.

## Révision

À revoir si on ajoute :
- Une app mobile native (le cookie ne marche pas → token JWT en stockage
  sécurisé OS, à arbitrer à ce moment-là).
- Une fédération d'identité (OAuth providers, SSO).
