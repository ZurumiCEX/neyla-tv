# Runbook — Configuration & test Cloudflare Stream

Procédure pour passer du mode FAKE (dev) à la vraie API Cloudflare Stream,
puis vérifier qu'un live OBS bout-en-bout fonctionne.

## 1. Informations à rassembler

Depuis le tableau de bord Cloudflare → **Stream** :

| Donnée | Où la trouver | Sensible ? |
|--------|---------------|------------|
| `CLOUDFLARE_ACCOUNT_ID` | URL du dashboard `dash.cloudflare.com/<account_id>` | Non (public) |
| `CLOUDFLARE_STREAM_SUBDOMAIN` | Stream → Settings → « Your subdomain » (`customer-XXXX.cloudflarestream.com`) | Non (public) |
| `CLOUDFLARE_API_TOKEN` | My Profile → API Tokens → **Create Token** → template « Stream / Read & Edit » (ou Custom : `Account · Stream · Edit`) | **Oui — secret** |
| `CLOUDFLARE_WEBHOOK_SECRET` | Généré par toi, à coller côté Cloudflare ET dans `.env` | **Oui — secret** |

## 2. Variables d'environnement

Édite ton `.env` (jamais commité) :

```env
CLOUDFLARE_ACCOUNT_ID=05995fd01991f050bfe0cd75769b84cf
CLOUDFLARE_STREAM_SUBDOMAIN=customer-8lv4hg99vlu3ckbc.cloudflarestream.com
CLOUDFLARE_API_TOKEN=<colle_ici_le_token_secret>
CLOUDFLARE_WEBHOOK_SECRET=<chaîne_aléatoire_>=32_caractères>
```

> ⚠ **Garde-fous** : ne commit jamais le token. Limite-le à la portée
> `Account · Stream · Edit`. Régénère-le si exposé.

## 3. Vérification automatique

Une commande dédiée crée puis supprime un `live_input` de test :

```bash
python manage.py verify_cloudflare_stream
```

Sortie attendue (mode prod) :

```
Configuration
  CLOUDFLARE_ACCOUNT_ID    : 05995fd0…
  CLOUDFLARE_API_TOKEN     : (défini, 40 car.)
  CLOUDFLARE_WEBHOOK_SECRET: (défini)

Création du live input « neyla-verify-... »
  ✓ live input créé
    uid              : 9c8f…
    rtmps_url        : rtmps://live.cloudflare.com:443/live/
    rtmps_key        : abcd…wxyz
    hls_playback_url : https://customer-8lv4hg99vlu3ckbc.cloudflarestream.com/.../manifest/video.m3u8

Suppression du live input
  ✓ live input supprimé

✓ Cloudflare Stream opérationnel.
```

Si le token est vide, la commande affiche `Mode FAKE actif` et utilise
les URLs `rtmps://fake.local/...` (ne touche pas Cloudflare).

## 4. Configurer le webhook

1. Cloudflare → **Stream → Webhooks** → ajoute l'URL publique
   `https://<ton-domaine>/api/webhooks/cloudflare-stream`.
2. Cloudflare génère un **signing secret** → copie-le dans
   `CLOUDFLARE_WEBHOOK_SECRET`.
3. Redémarre l'API pour que la nouvelle valeur soit lue.
4. Cloudflare propose un bouton « Send test event » : la requête doit
   répondre `200 ok`. Sinon vérifie les logs (signature invalide,
   timestamp drift > 5 min, ou UID inconnu — voir
   [`cloudflare-webhooks.md`](cloudflare-webhooks.md)).

## 5. Test end-to-end (OBS → Cloudflare → site)

1. **Approbation streamer** : sur l'admin, approuve la candidature d'un
   compte de test (ex. `streamer-test`). Le job `provision_channel`
   appelle Cloudflare et remplit `live_input_uid`, `rtmps_url`, `rtmps_key`
   et `hls_playback_url` sur la `Channel`.
2. **Récupère les identifiants RTMPS** : connecte-toi en streamer →
   page `/dashboard` → onglet « Diffuser ». Copie `rtmps_url` et `rtmps_key`.
3. **Configure OBS** :
   - Paramètres → Diffusion → Service = **Custom**.
   - Server = `rtmps_url` (ex. `rtmps://live.cloudflare.com:443/live/`).
   - Stream Key = `rtmps_key`.
   - Encodeur = x264, débit 3000–6000 kbps, 30/60 fps, keyframe 2 s.
4. **Démarrer le stream** dans OBS. Cloudflare reçoit le flux et appelle
   le webhook `live_input.connected` → la chaîne bascule `is_live=true`
   (visible sur la home, dans le menu Suivis, etc.).
5. **Lecture** : ouvre `/c/<slug>` dans un autre navigateur. Le
   `HlsPlayer` charge le manifest et joue la vidéo (latence ~10–20 s en
   mode standard, ~3 s en LL-HLS si activé côté Cloudflare).
6. **Arrêter le stream** dans OBS → webhook `live_input.disconnected` →
   `is_live=false`, la `StreamSession` se ferme.

## 6. Dépannage

| Symptôme | Cause probable | Fix |
|---|---|---|
| `verify_cloudflare_stream` → 401 | Token invalide / mauvaise portée | Régénère un token `Stream · Edit` |
| `verify_cloudflare_stream` → 404 | Account ID erroné | Recopie depuis l'URL du dashboard |
| Live démarre mais site reste hors-ligne | Webhook non reçu | Vérifie l'URL publique (HTTPS, joignable), les logs API, le secret |
| HLS 404 dans le navigateur | Channel pas provisionnée | Recolle l'URL `hls_playback_url` retournée par l'API ou re-trigger l'approbation |
| OBS « failed to connect » | RTMPS bloqué par le réseau / firewall | Tester sur réseau mobile, ou utiliser `rtmps://` port 443 |

## 7. Coûts

- **Live ingest** : facturé à la minute d'encodage Cloudflare.
- **Live playback** : facturé au volume de manifest + segments servis.
- Suivre dans Cloudflare → **Stream → Analytics**.
