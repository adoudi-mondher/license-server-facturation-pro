# Easy Facture License Server - Guide de déploiement

Guide complet pour déployer l'API de licences sur votre VPS Debian avec Docker.

## Prérequis

- VPS Debian (OVH) avec accès SSH
- Docker et Docker Compose installés
- Nginx Proxy Manager (déjà en place)
- DNS configuré : `api.easyfacture.mondher.ch` → IP du VPS

## Architecture

```
api.easyfacture.mondher.ch (HTTPS)
         ↓
Nginx Proxy Manager (port 443)
         ↓
FastAPI Container (port 8000)
         ↓
PostgreSQL Container (port 5432)
```

---

## Étape 1 : Préparer le serveur

### 1.1 Connexion SSH

```bash
ssh root@votre-ip-vps
```

### 1.2 Créer le répertoire de déploiement

```bash
mkdir -p /opt/easyfacture-license-server
cd /opt/easyfacture-license-server
```

---

## Étape 2 : Transférer les fichiers

Depuis votre machine locale (Windows) :

```bash
# Via SCP (depuis Git Bash ou PowerShell)
scp -r d:/workflow/python/license-server/* root@votre-ip-vps:/opt/easyfacture-license-server/

# OU via SFTP avec WinSCP / FileZilla
```

**Fichiers nécessaires :**
- `app/` (dossier complet)
- `main.py`
- `requirements.txt`
- `Dockerfile`
- `docker-compose.yml`
- `.env.example`

---

## Étape 3 : Configuration

### 3.1 Créer le fichier .env

Sur le VPS :

```bash
cd /opt/easyfacture-license-server
cp .env.example .env
nano .env
```

### 3.2 Remplir les valeurs

```env
# DATABASE
POSTGRES_USER=licenseuser
POSTGRES_PASSWORD=VotreMotDePasseFortetAleatoire123!
POSTGRES_DB=easyfacture_licenses

# SECURITY
SECRET_KEY=votre_cle_secrete_aleatoire_ici
LICENSE_SECRET_KEY=QvS9Dy6SjhpVPFf-nsu2NZ-xPfS3-Xaom--vwvdeH6w=

# API CONFIG
API_PORT=8000
ENVIRONMENT=production
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=*

# RATE LIMITING
TRIAL_RATE_LIMIT=3/hour
VALIDATE_RATE_LIMIT=100/hour

# TRIAL
DEFAULT_TRIAL_DAYS=30

# ADMIN
ADMIN_EMAIL=admin@mondher.ch
ADMIN_PASSWORD=VotreMotDePasseAdmin456!
```

**Générer SECRET_KEY :**

```bash
openssl rand -hex 32
```

---

## Étape 4 : Lancer l'application

### 4.1 Build et démarrage

```bash
cd /opt/easyfacture-license-server

# Build des images Docker
docker-compose build

# Démarrer les conteneurs
docker-compose up -d
```

### 4.2 Vérifier que tout fonctionne

```bash
# Vérifier les conteneurs
docker ps

# Voir les logs
docker-compose logs -f api

# Tester l'API localement
curl http://localhost:8000/health
```

**Réponse attendue :**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00"
}
```

---

## Étape 5 : Configurer Nginx Proxy Manager

### 5.1 Accéder à Nginx Proxy Manager

Ouvrir dans le navigateur : `http://votre-ip-vps:81`

### 5.2 Ajouter un Proxy Host

1. **Hosts** → **Add Proxy Host**

2. **Onglet Details :**
   - **Domain Names** : `api.easyfacture.mondher.ch`
   - **Scheme** : `http`
   - **Forward Hostname/IP** : `easyfacture-license-api` (nom du conteneur)
   - **Forward Port** : `8000`
   - **Cache Assets** : ✅ Activé
   - **Block Common Exploits** : ✅ Activé
   - **Websockets Support** : ❌ Désactivé

3. **Onglet SSL :**
   - **SSL Certificate** : Request a new SSL Certificate
   - **Force SSL** : ✅ Activé
   - **HTTP/2 Support** : ✅ Activé
   - **HSTS Enabled** : ✅ Activé
   - **Email** : `adoudi@mondher.ch`
   - **I Agree to the Let's Encrypt Terms** : ✅

4. **Save**

### 5.3 Attendre la génération du certificat SSL

Nginx Proxy Manager va automatiquement :
- Demander un certificat SSL à Let's Encrypt
- Configurer HTTPS
- Rediriger HTTP → HTTPS

---

## Étape 6 : Tester l'API publique

### 6.1 Test de santé

```bash
curl https://api.easyfacture.mondher.ch/health
```

**Réponse attendue :**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00"
}
```

### 6.2 Test de génération de licence trial

```bash
curl -X POST https://api.easyfacture.mondher.ch/api/v1/licenses/trial \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "machine_id": "abc123def456",
    "customer_name": "Test User",
    "company_name": "Test Company"
  }'
```

**Réponse attendue :**
```json
{
  "success": true,
  "message": "Licence d'essai générée avec succès",
  "license_key": "a1b2c3d4e5f6...",
  "expires_at": "2025-02-14T10:30:00",
  "license_type": "trial"
}
```

### 6.3 Test de validation

```bash
curl -X POST https://api.easyfacture.mondher.ch/api/v1/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "VOTRE_CLE_DE_LICENCE_ICI",
    "machine_id": "abc123def456"
  }'
```

---

## Étape 7 : Mise à jour de l'URL dans EasyFacture

### 7.1 Modifier config.py

Dans `facturation-app/config.py` :

```python
# Configuration du système de licence
LICENSE_API_URL = 'https://api.easyfacture.mondher.ch/api/v1'
```

### 7.2 Rebuild EasyFacture

```bash
cd facturation-app/packaging/windows
bash build.sh
```

---

## Commandes utiles

### Gestion des conteneurs

```bash
# Démarrer
docker-compose up -d

# Arrêter
docker-compose down

# Redémarrer
docker-compose restart

# Voir les logs
docker-compose logs -f

# Logs d'un service spécifique
docker-compose logs -f api
docker-compose logs -f postgres

# Rebuild après modification
docker-compose up -d --build
```

### Base de données

```bash
# Accéder à PostgreSQL
docker exec -it easyfacture-license-db psql -U licenseuser -d easyfacture_licenses

# Commandes SQL utiles
\dt                          # Lister les tables
SELECT * FROM licenses;      # Voir toutes les licences
SELECT * FROM activations;   # Voir toutes les activations
\q                           # Quitter
```

### Monitoring

```bash
# État des conteneurs
docker ps

# Utilisation des ressources
docker stats

# Espace disque
docker system df

# Nettoyer les images inutilisées
docker system prune -a
```

---

## Sécurité

### Firewall (UFW)

```bash
# Autoriser SSH
ufw allow 22/tcp

# Autoriser HTTP/HTTPS (Nginx Proxy Manager)
ufw allow 80/tcp
ufw allow 443/tcp

# Autoriser NPM Admin (temporaire)
ufw allow 81/tcp

# Activer le firewall
ufw enable

# Vérifier le status
ufw status
```

### Sauvegardes

```bash
# Sauvegarder la base de données
docker exec easyfacture-license-db pg_dump -U licenseuser easyfacture_licenses > backup_$(date +%Y%m%d).sql

# Restaurer
cat backup_20250115.sql | docker exec -i easyfacture-license-db psql -U licenseuser easyfacture_licenses
```

---

## Résolution de problèmes

### L'API ne démarre pas

```bash
# Vérifier les logs
docker-compose logs -f api

# Vérifier que PostgreSQL est démarré
docker ps | grep postgres

# Redémarrer tout
docker-compose down && docker-compose up -d
```

### Erreur de connexion à la base

```bash
# Vérifier les variables d'environnement
docker exec easyfacture-license-api env | grep DATABASE_URL

# Tester la connexion PostgreSQL
docker exec -it easyfacture-license-db psql -U licenseuser -d easyfacture_licenses
```

### Certificat SSL non généré

1. Vérifier que le DNS pointe bien vers le VPS : `nslookup api.easyfacture.mondher.ch`
2. Attendre 5-10 minutes (propagation DNS)
3. Vérifier les ports 80 et 443 ouverts : `ufw status`
4. Voir les logs NPM dans l'interface web

### Rate limit dépassé

```bash
# Modifier dans .env
TRIAL_RATE_LIMIT=10/hour

# Redémarrer
docker-compose restart api
```

---

## Maintenance

### Mise à jour de l'API

```bash
cd /opt/easyfacture-license-server

# Pull les nouvelles modifications
git pull  # si vous utilisez Git
# OU transférer les nouveaux fichiers via SCP

# Rebuild et redémarrer
docker-compose down
docker-compose build
docker-compose up -d

# Vérifier
docker-compose logs -f api
```

### Rotation des logs

Les logs Docker sont automatiquement gérés. Pour configurer la rotation :

Créer `/etc/docker/daemon.json` :

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Redémarrer Docker :

```bash
systemctl restart docker
```

---

## Support

En cas de problème :
- Email : adoudi@mondher.ch
- Logs : `docker-compose logs -f`
- Monitoring : https://api.easyfacture.mondher.ch/health

---

**Déploiement réalisé avec succès** ✅
