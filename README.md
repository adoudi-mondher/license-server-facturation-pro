# EasyFacture License Server

API REST pour la gestion des licences d'essai et commerciales de l'application EasyFacture.

Version: 1.0.0 (Phase 1 MVP)
Framework: FastAPI
Base de données: PostgreSQL
Python: 3.9+

Licence Open source - Pour les développeurs

---

## Table des matières

- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Endpoints API](#endpoints-api)
- [Déploiement](#déploiement)
- [Tests](#tests)
- [Roadmap](#roadmap)

---

## Architecture

Voir [ARCHITECTURE.md](ARCHITECTURE.md) pour la documentation complète.

Composants principaux:
- FastAPI: Framework web asynchrone
- PostgreSQL: Base de données relationnelle
- SQLAlchemy: ORM
- Cryptography: Chiffrement des licences (Fernet)
- SlowAPI: Rate limiting
- Pydantic: Validation des données

Structure du projet:
```
license-server/
├── app/
│   ├── api/              # Endpoints API
│   │   └── licenses.py   # Routes /trial, /validate
│   ├── models/           # Modèles SQLAlchemy
│   │   ├── license.py
│   │   ├── activation.py
│   │   ├── heartbeat.py
│   │   └── activation_code.py
│   ├── schemas/          # Schémas Pydantic
│   │   └── license.py
│   ├── utils/            # Utilitaires
│   │   └── license_crypto.py
│   ├── config.py         # Configuration
│   └── database.py       # Connexion BDD
├── main.py               # Point d'entrée
├── requirements.txt
└── .env.example
```

---

## Installation

### Prérequis

- Python 3.9+
- PostgreSQL 14+
- Git

### Étapes

1. Cloner le projet:
```bash
git clone https://github.com/adoudi-mondher/license-server.git
cd license-server
```

2. Créer un environnement virtuel:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Installer les dépendances:
```bash
pip install -r requirements.txt
```

4. Configurer la base de données:
```bash
# Créer la base PostgreSQL
createdb license_db

# Ou via psql
psql -U postgres
CREATE DATABASE license_db;
\q
```

5. Configurer l'environnement:
```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

---

## Configuration

### Fichier .env

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/license_db

# Security (IMPORTANT: Générer avec openssl rand -hex 32)
SECRET_KEY=votre-cle-secrete-ici
LICENSE_SECRET_KEY=votre-cle-licence-ici

# API
API_V1_PREFIX=/api/v1
PROJECT_NAME=EasyFacture License Server
ENVIRONMENT=development

# CORS
CORS_ORIGINS=http://localhost:3000,https://mondher.ch

# Rate Limiting
TRIAL_RATE_LIMIT=3/hour
VALIDATE_RATE_LIMIT=100/hour

# Trial
DEFAULT_TRIAL_DAYS=30
```

### Générer les clés secrètes

```bash
# SECRET_KEY (JWT)
openssl rand -hex 32

# LICENSE_SECRET_KEY (doit être identique à celle de EasyFacture client)
# Utiliser la même clé que dans generate_customer_license.py
```

---

## Utilisation

### Lancer le serveur de développement

```bash
python main.py
```

Ou avec uvicorn directement:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Le serveur démarre sur: http://127.0.0.1:8000

### Documentation interactive

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## Endpoints API

### 1. POST /api/v1/licenses/trial

Génère une licence d'essai (30 jours).

Rate limit: 3 requêtes/heure par IP

Request:
```json
{
  "email": "user@example.com",
  "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "customer_name": "Jean Dupont",
  "company_name": "Dupont SARL"
}
```

Response (200 OK):
```json
{
  "success": true,
  "message": "Licence d'essai générée avec succès",
  "license_key": "gAAAAABk...",
  "expires_at": "2025-02-15T10:30:00",
  "license_type": "trial"
}
```

Erreurs:
- 400: Trial déjà existante pour cet email ou machine
- 429: Rate limit dépassé

---

### 2. POST /api/v1/licenses/validate

Valide une clé de licence.

Rate limit: 100 requêtes/heure par IP

Request:
```json
{
  "license_key": "gAAAAABk...",
  "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
}
```

Response (200 OK):
```json
{
  "valid": true,
  "message": "Licence valide",
  "expires_at": "2025-02-15T10:30:00",
  "days_remaining": 25,
  "license_type": "trial"
}
```

Erreurs possibles:
- Licence invalide pour cette machine
- Licence expirée
- Licence révoquée
- Licence inactive

---

### 3. GET /

Endpoint racine (informations sur l'API).

Response:
```json
{
  "name": "EasyFacture License Server",
  "version": "1.0.0",
  "status": "online",
  "environment": "development"
}
```

---

### 4. GET /health

Health check pour monitoring.

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00"
}
```

---

## Déploiement

### Déploiement Docker (Recommandé)

Voir [QUICKSTART.md](QUICKSTART.md) pour le déploiement rapide en 5 minutes.
Voir [DEPLOYMENT.md](DEPLOYMENT.md) pour le guide complet.

1. Préparer l'environnement:
```bash
cp .env.example .env
# Éditer .env avec vos valeurs
```

2. Lancer le déploiement:
```bash
./deploy.sh
```

3. Vérifier le déploiement:
```bash
./check_deployment.sh https://api.easyfacture.mondher.ch
```

---

### Déploiement manuel VPS

Stack recommandée:
- OS: Ubuntu 22.04 LTS
- Web Server: Nginx (reverse proxy)
- Process Manager: systemd
- SSL: Let's Encrypt (Certbot)

Guide de déploiement:

1. Installer les dépendances système:
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql nginx certbot python3-certbot-nginx
```

2. Cloner le projet:
```bash
cd /var/www
sudo git clone https://github.com/adoudi-mondher/license-server.git
cd license-server
```

3. Configurer l'environnement:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Éditer .env avec les vraies valeurs
```

4. Créer le service systemd (/etc/systemd/system/license-api.service):
```ini
[Unit]
Description=EasyFacture License API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/license-server
Environment="PATH=/var/www/license-server/venv/bin"
ExecStart=/var/www/license-server/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000

[Install]
WantedBy=multi-user.target
```

5. Démarrer le service:
```bash
sudo systemctl daemon-reload
sudo systemctl start license-api
sudo systemctl enable license-api
sudo systemctl status license-api
```

6. Configurer Nginx (/etc/nginx/sites-available/license-api):
```nginx
server {
    listen 80;
    server_name api.easyfacture.mondher.ch;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

7. Activer le site:
```bash
sudo ln -s /etc/nginx/sites-available/license-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

8. Installer SSL (Let's Encrypt):
```bash
sudo certbot --nginx -d api.easyfacture.mondher.ch
```

L'API est maintenant accessible sur: https://api.easyfacture.mondher.ch

---

## Tests

Tests unitaires (Phase 1 - optionnel):

```bash
pytest tests/ -v
```

Test manuel avec curl:

```bash
# Test trial
curl -X POST https://api.easyfacture.mondher.ch/api/v1/licenses/trial \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "machine_id": "abc123...",
    "customer_name": "Test User"
  }'

# Test validation
curl -X POST https://api.easyfacture.mondher.ch/api/v1/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "gAAAAABk...",
    "machine_id": "abc123..."
  }'
```

---

## Roadmap

### Phase 1: MVP (Actuelle)
- API REST avec FastAPI
- Endpoints /trial et /validate
- Base PostgreSQL avec modèles
- Rate limiting
- Cryptographie compatible EasyFacture
- Déploiement Docker

### Phase 2: Production
- Dashboard admin (Flask-Admin ou React)
- Monitoring (logs, métriques)
- Backups automatiques
- Documentation Swagger complète
- Tests unitaires

### Phase 3: Heartbeat
- Endpoint /heartbeat
- Statistiques d'utilisation
- Dashboard analytics

### Phase 4: Avancé
- Support multi-produits
- Webhooks
- API partenaires
- Email automatique (trial expiré, upgrade)
- Système d'auto-update

---

## Support

Développeur: Mondher ADOUDI
Email: adoudi@mondher.ch
Documentation complète: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## Licence

Licence Open source - Pour les développeurs

---

Version: 1.0.0 - Janvier 2026
