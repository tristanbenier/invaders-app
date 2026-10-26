# Déploiement sur alwaysdata (offre gratuite)

Cible : l'offre gratuite d'alwaysdata (1 Go de disque, 256 Mo de RAM, 0,25 CPU), à l'adresse `https://moncompte.alwaysdata.net`. Remplace `moncompte` par le nom de ton compte partout ci-dessous.

Différences avec le guide VM (`deploy/README.md`) :

- pas de Caddy : le proxy d'alwaysdata gère HTTPS, et Django sert lui-même `/static/` (WhiteNoise) et `/media/` (`SERVE_FILES=True`) ;
- Gunicorn tourne comme site de type **Programme utilisateur** (`start.sh`) : un seul process et 4 threads, pour tenir dans 256 Mo ;
- la sauvegarde nocturne est une **tâche planifiée** alwaysdata ; les photos sont déjà couvertes par la sauvegarde quotidienne d'alwaysdata (3 jours sur l'offre gratuite).

## 1. Accès SSH et Python

1. Dans l'administration : **Accès distant → SSH**, active la connexion par mot de passe ou ajoute ta clé SSH.
2. **Environnement → Python** : choisis la version **3.14** par défaut.
3. Connecte-toi : `ssh moncompte@ssh-moncompte.alwaysdata.net`, puis vérifie que `python --version` affiche 3.14. Sur alwaysdata, utilise toujours `python`, jamais `python3`.

## 2. Installer l'application

```bash
git clone git@github.com:tristanbenier/invaders-app.git ~/invaders
python -m venv ~/invaders/backend/.venv
~/invaders/backend/.venv/bin/pip install -r ~/invaders/backend/requirements.txt
```

Le dépôt est privé : sur le serveur, génère une clé (`ssh-keygen -t ed25519`), puis ajoute `~/.ssh/id_ed25519.pub` comme *deploy key* en lecture seule dans les réglages du dépôt GitHub.

## 3. Configuration

```bash
cp ~/invaders/deploy/alwaysdata/env.example ~/invaders/.env
chmod 600 ~/invaders/.env
nano ~/invaders/.env   # moncompte, SECRET_KEY, contact
```

Génère la `SECRET_KEY` avec `python -c 'import secrets; print(secrets.token_urlsafe(50))'`.

## 4. Base de données

Pour une base vide :

```bash
cd ~/invaders/backend && .venv/bin/python manage.py migrate
```

Pour reprendre les données de ta machine (invaders, flashs, photos), sur ton Mac, depuis la racine du dépôt :

```bash
backend/.venv/bin/python -c "import sqlite3; s = sqlite3.connect('backend/db.sqlite3'); t = sqlite3.connect('/tmp/invaders.sqlite3'); s.backup(t)"
```

```bash
scp /tmp/invaders.sqlite3 moncompte@ssh-moncompte.alwaysdata.net:invaders/backend/db.sqlite3
```

```bash
rsync -az backend/media/ moncompte@ssh-moncompte.alwaysdata.net:invaders/backend/media/
```

La première commande fait une copie cohérente de la base, même si le serveur local tourne. Lance ensuite `migrate` sur le serveur.

## 5. Premier déploiement

```bash
~/invaders/deploy/alwaysdata/deploy.sh
```

Le script applique les migrations, collecte les fichiers statiques et vérifie la configuration (`check --deploy`). Le message « the site is not running » est normal à ce stade.

## 6. Créer le site

**Web → Sites → Ajouter un site** :

| Champ | Valeur |
|---|---|
| Adresses | `moncompte.alwaysdata.net` |
| Type | **Programme utilisateur** (*User program*) |
| Commande | `/home/moncompte/invaders/deploy/alwaysdata/start.sh` |
| Répertoire de travail | `/home/moncompte/invaders/backend` |

Dans l'onglet **SSL**, coche **Forcer HTTPS**. Django redirige aussi vers HTTPS (`X-Forwarded-Proto`).

Ouvre `https://moncompte.alwaysdata.net` : la page de connexion doit s'afficher. En cas d'erreur, regarde `~/admin/logs/sites/`.

## 7. Équipe et administrateur

```bash
cd ~/invaders/backend && .venv/bin/python manage.py createteam "Mon équipe" --email toi@example.org
```

La commande affiche le lien d'invitation du premier administrateur. Pour l'admin Django (`/admin/`), donne ensuite les droits à ton compte :

```bash
.venv/bin/python manage.py shell -c "from apps.accounts.models import User; User.objects.filter(email='toi@example.org').update(is_staff=True, is_superuser=True)"
```

Si tu as repris ta base locale, ces comptes existent déjà.

## 8. Sauvegarde de la base

**Avancé → Tâches planifiées → Ajouter** : type **Commande**, chaque jour à 3 h, avec la commande :

```bash
APP_DIR=/home/moncompte/invaders BACKUP_DIR=/home/moncompte/backups KEEP_DAYS=7 BACKUP_MEDIA=0 bash /home/moncompte/invaders/deploy/backup.sh
```

Elle fait une copie cohérente de la base SQLite (quelques Mo), ce que la sauvegarde de fichiers d'alwaysdata ne garantit pas pendant une écriture. Les photos sont exclues : elles prendraient environ 170 Mo par jour sur le quota de 1 Go.

## Mises à jour

Après un `git push` sur `main` (avec `frontend/dist` recompilé et commité, voir `deploy/README.md`) :

```bash
ssh moncompte@ssh-moncompte.alwaysdata.net invaders/deploy/alwaysdata/deploy.sh
```

Gunicorn recharge le code sans couper le site.

## Exploitation

| Besoin | Commande ou emplacement |
|---|---|
| Journaux de l'app et HTTP | `~/admin/logs/sites/` |
| Journaux des tâches planifiées | `~/admin/logs/jobs/` |
| Redémarrer | bouton **Redémarrer** dans **Web → Sites** |
| Place disque | `du -sh ~/invaders/backend/{media,tile_cache,.venv} ~/backups` |
| Vider le cache des tuiles | `cd ~/invaders/backend && .venv/bin/python manage.py prunetiles` |

À savoir sur l'offre gratuite :

- **Mise en veille** : alwaysdata arrête le site après 30 minutes sans visite. La visite suivante le relance en 2 à 3 secondes.
- **Mémoire** : un seul process Django. Si le compte dépasse 256 Mo, alwaysdata tue un process : le site redémarre à la visite suivante.
- **Import de photos** : l'import en masse depuis l'admin est lent avec 0,25 CPU. Pour beaucoup de photos, importe-les sur ta machine puis envoie `db.sqlite3` et `media/` (étape 4).
