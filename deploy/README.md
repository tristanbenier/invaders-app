# Déploiement en production

Cible : une petite VM Ubuntu 24.04 (par exemple Oracle Cloud « Always Free », ARM), avec :

- **Caddy** : HTTPS automatique, sert `/static/` et `/media/`, transmet le reste à Django ;
- **Gunicorn** (`backend/gunicorn.conf.py`) lancé par **systemd** (`invaders.service`) ;
- **SQLite**, les photos et le cache des tuiles sur le disque de la VM ;
- une **sauvegarde** chaque nuit (`invaders-backup.timer`).

Tous les chemins supposent l'application dans `/srv/invaders`, exécutée par l'utilisateur système `invaders`.

## 1. Créer la VM et ouvrir les ports

1. Crée une VM Ubuntu 24.04 et ajoute ta clé SSH.
2. Dans le réseau de la VM (Oracle : *Virtual Cloud Network → Security List*), autorise en entrée TCP **80** et **443** depuis `0.0.0.0/0`.
3. Les images Ubuntu d'Oracle bloquent aussi ces ports dans la VM. Une fois connecté en SSH :

   ```bash
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```

## 2. Nom de domaine

Fais pointer un nom vers l'IP publique de la VM, par exemple un sous-domaine gratuit [DuckDNS](https://www.duckdns.org) (`invaders-xxx.duckdns.org`). Caddy en a besoin pour obtenir le certificat HTTPS.

## 3. Installer les outils

```bash
sudo apt update && sudo apt install -y git python3-venv python3-dev build-essential
# Node.js 24 (pour construire l'app Vue)
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash - && sudo apt install -y nodejs
# Caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy
```

## 4. Installer l'application

```bash
sudo useradd --system --create-home --home-dir /srv/invaders-home --shell /usr/sbin/nologin invaders
sudo mkdir -p /srv/invaders /srv/invaders-backups && sudo chown invaders:invaders /srv/invaders /srv/invaders-backups
sudo -u invaders git clone https://github.com/tristanbenier/invaders-app.git /srv/invaders
sudo -u invaders python3 -m venv /srv/invaders/backend/.venv
```

Le dépôt est privé ? Utilise une *deploy key* GitHub en lecture seule pour l'utilisateur `invaders`.

## 5. Configuration

```bash
sudo -u invaders cp /srv/invaders/deploy/env.production.example /srv/invaders/.env
sudo -u invaders chmod 600 /srv/invaders/.env
sudo -u invaders nano /srv/invaders/.env   # domaine, SECRET_KEY, contact
```

Génère la `SECRET_KEY` avec `python3 -c 'import secrets; print(secrets.token_urlsafe(50))'`.

## 6. Services

```bash
sudo cp /srv/invaders/deploy/invaders.service /srv/invaders/deploy/invaders-backup.{service,timer} /etc/systemd/system/
sudo cp /srv/invaders/deploy/Caddyfile /etc/caddy/Caddyfile
echo 'INVADERS_DOMAIN=invaders-xxx.duckdns.org' | sudo tee /etc/default/caddy
sudo systemctl daemon-reload
sudo systemctl enable invaders invaders-backup.timer
```

## 7. Premier déploiement

```bash
sudo /srv/invaders/deploy/deploy.sh
sudo systemctl enable --now invaders-backup.timer
sudo systemctl restart caddy
```

Puis crée ton équipe : la commande affiche le lien d'invitation du premier administrateur.

```bash
cd /srv/invaders/backend && sudo -u invaders .venv/bin/python manage.py createteam "Mon équipe" --email toi@example.org
```

Pour l'admin Django (`/admin/`), donne ensuite les droits à ton compte :

```bash
sudo -u invaders .venv/bin/python manage.py shell -c "from apps.accounts.models import User; User.objects.filter(email='toi@example.org').update(is_staff=True, is_superuser=True)"
```

## Mises à jour

Après un `git push` sur `main` :

```bash
sudo /srv/invaders/deploy/deploy.sh
```

Le script récupère le code, installe les dépendances, reconstruit l'app Vue, applique les migrations, collecte les fichiers statiques, vérifie la configuration (`check --deploy`) et redémarre.

## Exploitation

| Besoin | Commande |
|---|---|
| Journaux de l'app | `journalctl -u invaders -f` |
| Journaux HTTP | `sudo tail -f /var/log/caddy/invaders.log` |
| Redémarrer | `sudo systemctl restart invaders` |
| Lancer une sauvegarde | `sudo systemctl start invaders-backup` |
| Sauvegardes | `/srv/invaders-backups` (14 jours) |
| Vider le cache des tuiles | `sudo -u invaders .venv/bin/python manage.py prunetiles` (automatique chaque jour sinon) |

**Restaurer une sauvegarde** : arrête l'app (`sudo systemctl stop invaders`), décompresse `db-….sqlite3.gz` vers `/srv/invaders/backend/db.sqlite3` (supprime les fichiers `-wal` et `-shm` à côté), extrais `media-….tar.gz` dans `/srv/invaders/backend`, puis relance.

Les sauvegardes restent sur la même VM : copie-les régulièrement ailleurs (stockage objet, autre machine) pour te protéger d'une perte de la VM.
