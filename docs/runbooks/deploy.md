# Runbook — Déploiement production

## Provisionnement initial du Droplet (one-time)

Hypothèses : Droplet DigitalOcean Ubuntu 24 LTS, Francfort ou Amsterdam,
2 vCPU / 4 Go RAM (cible budget < 30 USD/mois).

```bash
# 1. SSH root au premier boot, créer un user non-root + clé SSH.
adduser deploy && usermod -aG sudo deploy
mkdir -p /home/deploy/.ssh
# ... coller la clé publique ...
chown -R deploy:deploy /home/deploy/.ssh && chmod 700 /home/deploy/.ssh

# 2. Durcir SSH : désactiver password auth + root login dans /etc/ssh/sshd_config.
#    PasswordAuthentication no
#    PermitRootLogin no
systemctl restart sshd

# 3. ufw : autoriser 22, 80 uniquement. Pas de 443 : Cloudflare termine TLS et
#    relaie en HTTP via le proxy orange.
ufw allow 22/tcp && ufw allow 80/tcp && ufw enable

# 4. Installer Docker + Compose v2.
curl -fsSL https://get.docker.com | sh
usermod -aG docker deploy

# 5. Cloner le dépôt.
mkdir -p /opt/neyla && chown deploy:deploy /opt/neyla
sudo -u deploy git clone https://github.com/ZurumiCEX/neyla-tv.git /opt/neyla

# 6. Créer /opt/neyla/.env à partir de .env.example, le remplir avec les vrais
#    secrets (Cloudflare, Spaces, Sentry, Postgres). chmod 600.
cp /opt/neyla/.env.example /opt/neyla/.env && nano /opt/neyla/.env
chmod 600 /opt/neyla/.env

# 7. Pointer le DNS Cloudflare : enregistrement A `app.<domaine>` → IP du Droplet,
#    proxy orange (TLS automatique).

# 8. Premier build + démarrage.
cd /opt/neyla
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env build
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env up -d
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env \
    exec -T api python manage.py migrate
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env \
    exec -T api python manage.py loaddata catalog/fixtures/games_seed.json
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env \
    exec -T api python manage.py createsuperuser
```

## Déploiement continu (automatique via GitHub Actions)

À chaque push sur `main`, le workflow `.github/workflows/deploy.yml` :

1. SSH sur le Droplet avec la clé `DEPLOY_SSH_KEY`.
2. `git pull --ff-only` dans `$DEPLOY_PATH`.
3. `docker compose ... build` puis `up -d` (recrée seulement les services qui ont changé).
4. `python manage.py migrate --noinput`.
5. `docker system prune -f` pour nettoyer les vieilles images.

### Secrets GitHub Actions requis

| Secret             | Exemple                          |
|--------------------|----------------------------------|
| `DEPLOY_HOST`      | `203.0.113.42`                   |
| `DEPLOY_USER`      | `deploy`                         |
| `DEPLOY_PORT`      | `22` (optionnel)                 |
| `DEPLOY_SSH_KEY`   | contenu de `~/.ssh/id_ed25519`   |
| `DEPLOY_PATH`      | `/opt/neyla`                     |

## Déploiement manuel

Si la CI est cassée et qu'il faut livrer en urgence :

```bash
ssh deploy@droplet
cd /opt/neyla
git pull --ff-only
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env build
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env up -d
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env \
    exec -T api python manage.py migrate --noinput
```

## Rollback

```bash
ssh deploy@droplet
cd /opt/neyla
# Identifier le dernier bon commit.
git log --oneline -20
git checkout <SHA_BON>
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env build
docker compose -f infra/compose/docker-compose.prod.yml --env-file .env up -d
# Si une migration a été ajoutée et qu'il faut revenir en arrière côté DB,
# il faut soit re-jouer la migration inverse explicitement, soit restore
# depuis un dump (cf. restore-postgres.md).
```

Préférer **`git revert` du commit problématique sur main + nouveau deploy**
plutôt qu'un rollback DB qui peut perdre des données utilisateur.

## Vérifications post-deploy

1. `curl -sS https://app.<domaine>/healthz` → `ok` (nginx).
2. `curl -sS https://app.<domaine>/api/healthz` → `{"status":"ok",...}`.
3. Ouvrir la home, vérifier qu'au moins une chaîne s'affiche si attendu.
4. Vérifier le dashboard Sentry pour pic d'erreurs anormal sur les 5 dernières min.
