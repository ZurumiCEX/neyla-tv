# ADR 009 — Réactivation du worker Celery (asynchrone) + Valkey managé

- **Statut** : Proposée
- **Date** : 2026-05-28
- **Complète** : [ADR 008 — App Platform](008-app-platform.md)

## Contexte

Au lancement sur App Platform, le worker et le beat Celery ont été **désactivés**
côté console : le plan Upstash Redis (free) ne tenait pas la charge Celery
(connexions, OOM, `exit code 128`). Pour rester fonctionnels sans worker, les
traitements ont été rendus **synchrones avec repli** :

- provisionnement de chaîne à l'approbation streamer (appel direct) ;
- notifications (création directe, `bulk_create` pour le live) ;
- gamification et messagerie support (best-effort, jamais bloquant) ;
- emails de vérification/réinitialisation : `.delay()` mais worker absent → non
  envoyés tant que le worker n'est pas là.

La v2 a ajouté des besoins **réellement périodiques** qui n'ont pas d'équivalent
synchrone naturel :

- **renouvellement/expiration des abonnements** (`process_due_subscriptions`),
  désormais exposé en tâche (`subscriptions.tasks.process_due_subscriptions_task`)
  et planifié (`config/celery.py` → `beat_schedule`, quotidien 03:00).

## Décision

Réactiver `worker` + `beat` **une fois un Redis/Valkey managé** disponible
(capable de tenir Celery), sans retirer les replis synchrones (filet de
sécurité si le worker tombe).

### Étapes

1. **Provisionner un Valkey/Redis managé** (DigitalOcean Managed Valkey, ou
   équivalent tenant les connexions Celery). Une seule URL `rediss://` sert
   déjà channels + chat + Celery (cf. `.do/app.yaml`).
2. **Activer les composants** `worker` et `beat` (déjà déclarés dans
   `.do/app.yaml`, `run_command` :
   `celery -A config worker -l info --pool=solo` et `celery -A config beat -l info`).
   Le beat lit `app.conf.beat_schedule` (scheduler par défaut, pas besoin de
   `django_celery_beat` côté ordonnanceur).
3. **Vérifier** : `ping` task répond `pong` ; un abonnement échu est renouvelé
   ou expiré au passage du beat ; les emails partent.
4. **Garder les replis** synchrones tels quels (idempotents).

### Conséquences

- **+** Renouvellements d'abonnement automatiques ; emails envoyés ; base prête
  pour les tâches lourdes (notifications de masse, recalculs analytics).
- **+** Pas de régression si worker indisponible : le code synchrone reste la
  source de vérité immédiate.
- **−** Coût d'un Valkey managé ; surface ops (supervision du worker/beat).
- **−** Risque de double-exécution beat si plusieurs instances beat → garder
  **une seule** instance `beat`.

## Alternatives écartées

- **Cron externe appelant `manage.py process_subscriptions`** : possible et sans
  worker, mais ne couvre pas emails/tâches futures ; conservé comme repli manuel.
- **Rester 100 % synchrone** : impossible pour le périodique (renouvellements).

## Suivi

- [ ] Provisionner Valkey managé, poser l'URL `rediss://`.
- [ ] Activer `worker` + `beat` (1 instance beat).
- [ ] Valider renouvellement d'abonnement + envoi d'emails de bout en bout.
