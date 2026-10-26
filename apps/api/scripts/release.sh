#!/bin/sh
# Étape de release (Fly.io, avant chaque déploiement) : vérifications, migrations,
# puis comptes démo si SEED_DEMO=1. Chaque étape est annoncée dans les logs.
# Aucun secret n'est affiché : seulement « défini » / « absent ».
#
# En cas d'échec, on attend RELEASE_FAIL_WAIT secondes (15 par défaut) avant de
# quitter : sinon Fly détruit la machine avant d'avoir récupéré les logs
# (« timeout waiting for release command logs »).
set -eu

step="démarrage"

on_exit() {
  code=$?
  if [ "$code" -ne 0 ]; then
    echo "[release] ÉCHEC à l'étape : $step (code $code)"
    echo "[release] Pour voir le détail dans ton terminal :"
    echo "  fly machine run <image du deploy> sh /app/scripts/diagnose.sh --rm -a ${FLY_APP_NAME:-neyla-tv}"
    echo "[release] Secrets définis : fly secrets list -a ${FLY_APP_NAME:-neyla-tv}"
    sleep "${RELEASE_FAIL_WAIT:-15}"
  fi
  exit "$code"
}
trap on_exit EXIT

state() { if [ -n "$(printenv "$1" 2>/dev/null)" ]; then echo "défini"; else echo "absent"; fi; }

step="vérification de la configuration"
echo "[release] app : ${FLY_APP_NAME:-?} · réglages : ${DJANGO_SETTINGS_MODULE:-?}"
for name in DJANGO_SECRET_KEY DATABASE_URL REDIS_URL CELERY_BROKER_URL FRONTEND_URL \
  DJANGO_CORS_ALLOWED_ORIGINS WEBAUTHN_RP_ID WEBAUTHN_ORIGINS; do
  echo "[release]   $name : $(state "$name")"
done

missing=""
[ -n "${DJANGO_SECRET_KEY:-}" ] || missing="$missing DJANGO_SECRET_KEY"
if [ -z "${DATABASE_URL:-}" ] && [ "${POSTGRES_HOST:-postgres}" = "postgres" ]; then
  missing="$missing DATABASE_URL"
fi
if [ -n "$missing" ]; then
  echo "[release] ERREUR : secret(s) manquant(s) :$missing"
  for name in $missing; do
    case "$name" in
      DJANGO_SECRET_KEY)
        echo "  fly secrets set DJANGO_SECRET_KEY=\"\$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')\" -a ${FLY_APP_NAME:-neyla-tv}"
        ;;
      DATABASE_URL)
        echo "  fly secrets set DATABASE_URL=\"postgresql://user:motdepasse@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require\" -a ${FLY_APP_NAME:-neyla-tv}"
        ;;
    esac
  done
  exit 1
fi

step="preflight (base de données, Redis)"
python manage.py preflight 2>&1

step="migrations"
echo "[release] migrations…"
python manage.py migrate --noinput 2>&1

if [ "${SEED_DEMO:-0}" = "1" ]; then
  step="données de démonstration"
  echo "[release] données de démonstration (seed_demo)…"
  # La démo ne doit jamais bloquer un déploiement : en cas d'échec, on prévient.
  python manage.py seed_demo 2>&1 || echo "[release] attention : seed_demo a échoué (voir ci-dessus), déploiement poursuivi."
fi

step="terminé"
echo "[release] terminé ✓"
