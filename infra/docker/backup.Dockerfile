# Conteneur backup : pg_dump quotidien vers DO Spaces (S3-compat) via cron.
FROM postgres:16-alpine

RUN apk add --no-cache aws-cli busybox-suid

COPY infra/scripts/backup-postgres.sh /usr/local/bin/backup-postgres
RUN chmod +x /usr/local/bin/backup-postgres

COPY infra/docker/backup.crontab /etc/crontabs/root

# Foreground cron, logs vers stdout (-l 8 = niveau verbeux).
CMD ["crond", "-f", "-l", "8"]
