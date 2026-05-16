#!/bin/sh
# Dump Postgres → gzip → upload DO Spaces (compatible S3 via aws-cli).
# Variables d'env attendues :
#   POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
#   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
#   BACKUPS_BUCKET (ex: neyla-backups)
#   SPACES_ENDPOINT (ex: https://fra1.digitaloceanspaces.com)
#
# Rétention : laisser une lifecycle rule sur le bucket DO Spaces
# (suppression > 30 jours). Plus fiable qu'un nettoyage scripté.

set -eu

: "${POSTGRES_HOST:?missing}"
: "${POSTGRES_DB:?missing}"
: "${POSTGRES_USER:?missing}"
: "${POSTGRES_PASSWORD:?missing}"
: "${BACKUPS_BUCKET:?missing}"
: "${SPACES_ENDPOINT:?missing}"

TS=$(date -u +%Y%m%d-%H%M%S)
FILE="/tmp/neyla-${TS}.sql.gz"

echo "[backup] $(date -u) starting dump of ${POSTGRES_DB}"
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
    -h "${POSTGRES_HOST}" \
    -U "${POSTGRES_USER}" \
    -d "${POSTGRES_DB}" \
    --no-owner --no-privileges \
    | gzip -9 > "${FILE}"

SIZE=$(wc -c < "${FILE}")
echo "[backup] dump size=${SIZE} bytes"

aws s3 cp "${FILE}" \
    "s3://${BACKUPS_BUCKET}/postgres/neyla-${TS}.sql.gz" \
    --endpoint-url "${SPACES_ENDPOINT}"

rm -f "${FILE}"
echo "[backup] $(date -u) done"
