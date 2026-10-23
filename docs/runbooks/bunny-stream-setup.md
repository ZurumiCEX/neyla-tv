# Runbook : configurer et tester Bunny Stream

Cette procédure fait passer le projet du mode FAKE (dev) à la vraie API Bunny Stream,
puis vérifie de bout en bout le parcours OBS → Bunny → site. Les choix
d'architecture sont décrits dans l'[ADR 010](../adr/010-bunny-stream.md).

## 1. Informations à rassembler

Elles se trouvent sur bunny.net → **Stream**, dans ta *Video Library*, page **API** :

| Variable | Où la trouver | Sensible ? |
|----------|---------------|------------|
| `BUNNY_STREAM_LIBRARY_ID` | « Video Library ID » | Non |
| `BUNNY_STREAM_API_KEY` | « API Key » (AccessKey de la bibliothèque) | **Oui, secret** |
| `BUNNY_STREAM_CDN_HOSTNAME` | « CDN Hostname » (`vz-xxxxxxxx-xxx.b-cdn.net`) | Non |
| `BUNNY_STREAM_WEBHOOK_KEY` | « Read-Only API Key », qui sert à vérifier `X-BunnyStream-Signature` | **Oui, secret** |
| `BUNNY_STREAM_RTMP_URL` | Optionnel : URL d'ingest RTMP, si l'API ne la renvoie pas | Non |

> La clé du compte bunny.net (*Account API key*) **ne fonctionne pas** pour l'API
> Stream. Utilise la clé de la **bibliothèque**.

Le live (Stream Live) doit être activé sur le compte Bunny.

## 2. Variables d'environnement

Mets-les dans le `.env` local, qui n'est jamais commité, ou dans la console
DigitalOcean (type *Encrypted*) :

```env
BUNNY_STREAM_LIBRARY_ID=123456
BUNNY_STREAM_API_KEY=<secret>
BUNNY_STREAM_CDN_HOSTNAME=vz-xxxxxxxx-xxx.b-cdn.net
BUNNY_STREAM_WEBHOOK_KEY=<read-only key>
STREAM_STATUS_POLL_SECONDS=20
```

## 3. Vérification automatique

```bash
python manage.py verify_bunny_stream
```

La commande :

1. crée un live stream de test ;
2. affiche `stream_id`, `ingest_url`, la clé masquée, `playback_url` et la réponse
   brute de Bunny ;
3. lit l'état du flux ;
4. supprime le live stream.

Le message `✓ Bunny Stream opérationnel.` confirme que tout est bien branché.

| Erreur | Cause | Correction |
|--------|-------|------------|
| `401` | Mauvaise clé (clé du compte au lieu de celle de la bibliothèque) | Recopier l'API Key depuis la page API de la bibliothèque |
| `404` | Library ID erroné, ou Stream Live non activé | Vérifier l'ID ; demander l'activation du live à Bunny |
| `⚠ clé ou URL de lecture absente` | Champ nommé autrement dans la réponse brute | Ajouter ce nom dans `channels_app/bunny.py` (`create_live_stream`) |

## 4. Webhook (Shorts / « Instant »)

1. Bunny → Stream → ta bibliothèque → **Webhook URL** :
   `https://<ton-domaine>/api/webhooks/bunny/stream`
2. `BUNNY_STREAM_WEBHOOK_KEY` doit être la clé utilisée par Bunny pour signer
   l'en-tête `X-BunnyStream-Signature`.
3. Pour tester, uploade un Short depuis le dashboard. Il doit passer de *processing*
   à *ready* une fois l'encodage fini (statut 3).

L'état **live** ne dépend pas du webhook. Il est synchronisé par le job
`channels_app.tasks.sync_live_status`, lancé par Celery beat : le service `beat`
doit donc tourner.

## 5. Test de bout en bout (OBS → Bunny → site)

1. **Approuver** la candidature d'un compte de test dans l'admin. Le live stream
   Bunny est alors créé, et `stream_id`, `ingest_url`, `stream_key` et
   `playback_url` sont remplis.
2. **Dashboard → Diffusion** : copier le serveur RTMP et la clé de stream.
3. **OBS** :
   - Paramètres → Flux → Service *Personnalisé* ;
   - Serveur et Clé : coller les valeurs copiées ;
   - Sortie : x264, keyframe à 2 s. Débit : 2 500 kbps en 720p30 sur 4G, 4 500 kbps
     en 1080p30 sur la fibre.
4. **Démarrer le streaming**. Dans les `STREAM_STATUS_POLL_SECONDS` qui suivent, la
   chaîne passe `is_live=true`. Le bouton « Tester la connexion » ou « Passer en
   direct » accélère la bascule.
5. Ouvrir `/c/<slug>` dans un autre navigateur : le lecteur HLS joue.
6. **Arrêter** OBS : la chaîne repasse hors ligne au passage suivant, et la session
   se clôt.

## 6. Dépannage

| Symptôme | Cause probable | Correction |
|----------|----------------|------------|
| La chaîne ne passe jamais live | `beat` arrêté, ou clé API vide (mode FAKE) | Vérifier le service `beat` et lancer `verify_bunny_stream` |
| Le lecteur affiche « Connexion au flux… » | Encodage Bunny en cours (5 à 15 s) | Attendre : le lecteur réessaie tout seul |
| HLS 403 | Token authentication du CDN activée côté Bunny | La désactiver pour la bibliothèque live, ou signer les URL |
| Short bloqué en *processing* | Webhook non reçu (URL ou clé) | Vérifier l'URL publique HTTPS et `BUNNY_STREAM_WEBHOOK_KEY` |

## 7. Coûts

Bunny facture le stockage, la bande passante CDN et l'encodage. Le suivi se fait
dans Bunny → Stream → **Statistics**.
