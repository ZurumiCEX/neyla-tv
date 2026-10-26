#!/bin/sh
# Diagnostic sans aucune écriture (pas de migration, pas de démo), à lancer à la main :
#   fly machine run <image> sh /app/scripts/diagnose.sh --rm -a neyla-tv
# La sortie s'affiche directement dans le terminal. Aucun secret n'est imprimé.
set -u

state() { if [ -n "$(printenv "$1" 2>/dev/null)" ]; then echo "défini"; else echo "absent"; fi; }

echo "[diagnostic] app : ${FLY_APP_NAME:-?} · région : ${FLY_REGION:-?} · réglages : ${DJANGO_SETTINGS_MODULE:-?}"
for name in DJANGO_SECRET_KEY DATABASE_URL REDIS_URL CELERY_BROKER_URL CELERY_RESULT_BACKEND \
  FRONTEND_URL DJANGO_CORS_ALLOWED_ORIGINS WEBAUTHN_RP_ID WEBAUTHN_ORIGINS SEED_DEMO; do
  echo "[diagnostic]   $name : $(state "$name")"
done

if [ -z "${DJANGO_SECRET_KEY:-}" ]; then
  echo "[diagnostic] ERREUR : DJANGO_SECRET_KEY absent — les réglages de production ne peuvent pas se charger."
  exit 1
fi

echo "[diagnostic] vérification Django…"
if ! python manage.py preflight 2>&1; then
  echo "[diagnostic] → corrige les points ci-dessus puis relance fly deploy."
  exit 1
fi

echo "[diagnostic] migrations en attente (rien n'est appliqué) :"
python manage.py showmigrations --plan 2>&1 | grep -v "\[X\]" | tail -n 30 || true
echo "[diagnostic] terminé ✓ — si fly deploy échoue encore, l'erreur vient des migrations : colle ces lignes."
