# Runbook — Incident production (5 min)

À suivre dans l'ordre dès qu'un incident est suspecté (alerte Sentry, plaintes,
healthcheck rouge).

## 1. Constat (30 s)

```bash
# Health public.
curl -sS https://app.<domaine>/healthz       # → 200 "ok" si nginx vivant
curl -sS https://app.<domaine>/api/healthz   # → 200 {"status":"ok",...}
```

- nginx KO mais site OK Cloudflare : panne réseau Droplet ou DNS.
- nginx OK mais `/api/healthz` 503 : Postgres ou Redis down.
- `/api/healthz` 200 mais erreurs Sentry : bug applicatif récent.

## 2. État des conteneurs (30 s)

```bash
ssh deploy@droplet
cd /opt/neyla
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env ps
```

Tous les services doivent être `Up` et healthy. Si l'un est `Restarting`,
regarder les logs immédiatement.

## 3. Logs ciblés (1 min)

```bash
# Tous les logs des 5 dernières minutes.
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env \
    logs --tail=200 --since=5m

# Un service en particulier.
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env \
    logs --tail=200 api
```

Logs en prod = JSON. `jq` peut aider :
```bash
docker compose ... logs --tail=500 api | jq -r 'select(.level=="ERROR") | .msg' 2>/dev/null
```

## 4. Action immédiate (2 min)

| Symptôme                            | Action                                                                 |
|-------------------------------------|------------------------------------------------------------------------|
| Service en boucle de restart        | `docker compose ... logs <svc>` puis fix ou `restart <svc>`           |
| Postgres KO                         | `restart postgres` ; si volume corrompu → cf. restore-postgres.md      |
| Redis KO                            | `restart redis` (les messages chat éphémères, OK)                      |
| Erreur déploy récent                | rollback `git checkout <SHA_PRECEDENT>` puis rebuild (cf. deploy.md)    |
| Webhooks Cloudflare en boucle 4xx   | vérifier `CLOUDFLARE_WEBHOOK_SECRET` + horloge NTP du Droplet          |
| Latence anormale                    | `docker stats` ; tuer process zombie (`docker exec ... ps aux`)        |

```bash
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env restart api
```

## 5. Communication (1 min)

- Mettre à jour le statut côté Cloudflare (page de statut si on en a une).
- Si downtime > 5 min, prévenir les streamers principaux par mail/discord.

## 6. Post-mortem

Après résolution, dans la même semaine :
- Note dans `docs/runbooks/incidents/YYYY-MM-DD-<titre>.md` :
  - Chronologie (UTC).
  - Cause racine.
  - Ce qui a manqué pour détecter plus tôt.
  - Action de mitigation (alerte, healthcheck, test, runbook).

## Numéros utiles

- Sentry dashboard : `https://sentry.io/organizations/<org>/issues/`
- Cloudflare dashboard : `https://dash.cloudflare.com`
- DigitalOcean dashboard : `https://cloud.digitalocean.com`
- DO Spaces backups : `https://cloud.digitalocean.com/spaces/<bucket>`
