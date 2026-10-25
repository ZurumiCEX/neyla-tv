#!/bin/sh
# Étape de release (Fly.io, avant chaque déploiement) : vérifications, migrations,
# puis comptes démo si SEED_DEMO=1. Chaque étape est annoncée dans les logs
# (fly logs) pour savoir immédiatement ce qui manque. Aucun secret n'est affiché.
set -eu

echo "[release] vérification de la configuration…"
missing=""
[ -n "${DJANGO_SECRET_KEY:-}" ] || missing="$missing DJANGO_SECRET_KEY"
if [ -z "${DATABASE_URL:-}" ] && [ "${POSTGRES_HOST:-postgres}" = "postgres" ]; then
  missing="$missing DATABASE_URL"
fi
if [ -n "$missing" ]; then
  echo "[release] ERREUR : secret(s) manquant(s) :$missing"
  echo "[release] Ajoute-les puis relance « fly deploy », par exemple :"
  for name in $missing; do
    case "$name" in
      DJANGO_SECRET_KEY)
        echo "  fly secrets set DJANGO_SECRET_KEY=\"\$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')\""
        ;;
      DATABASE_URL)
        echo "  fly secrets set DATABASE_URL=\"postgresql://user:motdepasse@ep-xxx.eu-central-1.aws.neon.tech/neondb?sslmode=require\""
        ;;
    esac
  done
  exit 1
fi

python manage.py preflight

echo "[release] migrations…"
python manage.py migrate --noinput

if [ "${SEED_DEMO:-0}" = "1" ]; then
  echo "[release] données de démonstration (seed_demo)…"
  # La démo ne doit jamais bloquer un déploiement : en cas d'échec, on prévient.
  python manage.py seed_demo || echo "[release] attention : seed_demo a échoué (voir ci-dessus), déploiement poursuivi."
fi

echo "[release] terminé ✓"
