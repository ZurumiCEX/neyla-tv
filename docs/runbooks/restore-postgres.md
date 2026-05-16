# Runbook — Restaurer un dump Postgres

Les dumps quotidiens sont stockés sur DigitalOcean Spaces, sous
`s3://<BACKUPS_BUCKET>/postgres/neyla-<YYYYMMDD-HHMMSS>.sql.gz`,
avec une lifecycle rule à 30 jours.

## 1. Identifier le dump à restaurer

```bash
ssh deploy@droplet
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env \
    exec -T backup \
    aws s3 ls "s3://${BACKUPS_BUCKET}/postgres/" \
    --endpoint-url "${SPACES_ENDPOINT}"
```

Repérer la ligne du dump voulu, par exemple :
```
2026-05-15 03:00:12  4.2 MB neyla-20260515-030012.sql.gz
```

## 2. Télécharger le dump localement (sur le Droplet)

```bash
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env \
    exec -T backup \
    aws s3 cp "s3://${BACKUPS_BUCKET}/postgres/neyla-20260515-030012.sql.gz" - \
    --endpoint-url "${SPACES_ENDPOINT}" > /tmp/restore.sql.gz
```

## 3. Stopper l'app (mais pas Postgres)

```bash
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env \
    stop api worker beat web
```

## 4. Drop + recréer la base, puis restore

```bash
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env \
    exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" postgres \
    psql -U "$POSTGRES_USER" -d postgres \
    -c "DROP DATABASE IF EXISTS $POSTGRES_DB;" \
    -c "CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;"

gunzip -c /tmp/restore.sql.gz | docker compose -f infra/compose/docker-compose.prod.yml \
    --env-file .env exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" postgres \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

## 5. Re-démarrer l'app

```bash
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env \
    up -d
# Les migrations sont déjà dans le dump : pas besoin de re-migrer.
```

## 6. Validation

```bash
curl -sS https://app.<domaine>/api/healthz
# Vérifier qu'on peut se connecter avec un compte existant.
# Vérifier le compteur de chaînes en admin.
```

## Restauration locale (debug)

Sur poste local, pour examiner un dump sans toucher la prod :

```bash
# Récupérer le dump localement (avec credentials Spaces) :
aws s3 cp "s3://neyla-backups/postgres/neyla-20260515-030012.sql.gz" /tmp/ \
    --endpoint-url https://fra1.digitaloceanspaces.com

# Restore dans Postgres local de dev :
make down && make up
gunzip -c /tmp/neyla-20260515-030012.sql.gz | docker compose -f infra/compose/docker-compose.yml \
    --env-file .env exec -T -e PGPASSWORD=neyla postgres \
    psql -U neyla -d neyla
```
