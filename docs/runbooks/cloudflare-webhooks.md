# Runbook — Webhooks Cloudflare Stream

## Endpoint exposé

```
POST https://api.<domain>/api/webhooks/cloudflare/stream
```

## Format de signature attendu

Header :

```
Webhook-Signature: time=<unix_seconds>,sig1=<hex_sha256>
```

avec :

```
sig1 = HMAC_SHA256(secret = CLOUDFLARE_WEBHOOK_SECRET,
                   payload = f"{time}.{raw_body}")
```

Tolérance de fraîcheur : **5 minutes** (anti-rejeu). Comparaison via
`hmac.compare_digest`.

## Événements traités

| `eventType`               | Action côté Django                                              |
|---------------------------|------------------------------------------------------------------|
| `live_input.connected`    | `channel.is_live = True`, `last_live_started_at = now`, notif Celery |
| `live_input.disconnected` | `channel.is_live = False`                                        |
| autres                    | log info, ignoré                                                 |

L'identification de la chaîne se fait via `data.live_input_uid` (ou `data.uid`).
Si l'UID est inconnu côté DB → log warn + 200 (on ne renvoie pas 4xx pour
ne pas mettre Cloudflare en retry infini).

## Configuration côté Cloudflare

1. Dans le dashboard Cloudflare → **Stream** → **Webhooks** (ou via API
   `PUT /accounts/<id>/stream/webhook`).
2. URL : `https://api.<domain>/api/webhooks/cloudflare/stream`.
3. Récupérer le secret renvoyé par Cloudflare et le poser en variable
   d'environnement côté Droplet :

   ```
   CLOUDFLARE_WEBHOOK_SECRET=<secret>
   ```
4. Redémarrer le service `api` (`make up` ou `systemctl restart`).

## Régénérer le secret

1. Régénérer depuis le dashboard Cloudflare.
2. Mettre à jour la variable `CLOUDFLARE_WEBHOOK_SECRET` sur le Droplet.
3. **Pendant la fenêtre de bascule** (5 min) : Cloudflare envoie avec le
   nouveau secret, Django attend le nouveau — pas de double-secret pour
   le MVP. Faire la rotation hors heures de pointe.

## Tester en local (mode FAKE)

Le mode FAKE n'envoie pas de webhooks. Pour simuler manuellement :

```bash
SECRET=dev-webhook-secret
TS=$(date +%s)
BODY='{"eventType":"live_input.connected","data":{"live_input_uid":"fake-XXXX"}}'
SIG=$(printf '%s.%s' "$TS" "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')
curl -X POST http://localhost:8000/api/webhooks/cloudflare/stream \
  -H "Content-Type: application/json" \
  -H "Webhook-Signature: time=$TS,sig1=$SIG" \
  -d "$BODY"
```

## En cas de souci

- **400 signature invalide** : vérifier que `CLOUDFLARE_WEBHOOK_SECRET`
  côté Django correspond à celui posté par Cloudflare. Vérifier l'horloge
  du Droplet (NTP) : un décalage > 5 min fait échouer la signature.
- **200 mais rien ne se passe** : l'UID n'est pas associé à une chaîne.
  Vérifier que la chaîne a bien été provisionnée
  (`Channel.objects.filter(live_input_uid=...)`).
- **Retry storm Cloudflare** : ne jamais renvoyer 5xx sur ce endpoint à
  moins d'une vraie panne — Cloudflare réessaie.
