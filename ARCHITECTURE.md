# 🏗️ Architecture - Serveur de Licences EasyFacture

**Version** : 1.0.0
**Date** : 31 Décembre 2025
**Status** : Design Phase

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Objectifs](#objectifs)
3. [Architecture système](#architecture-système)
4. [API REST](#api-rest)
5. [Modèle de données](#modèle-de-données)
6. [Sécurité](#sécurité)
7. [Déploiement](#déploiement)
8. [Roadmap](#roadmap)

---

## 🎯 Vue d'ensemble

### Problème à résoudre

Actuellement, le système de licences d'EasyFacture fonctionne **hors ligne** :
- ❌ Le vendeur doit manuellement générer chaque licence
- ❌ Pas de version trial automatique
- ❌ Pas de statistiques d'utilisation
- ❌ Difficile de révoquer une licence
- ❌ Pas de gestion centralisée

### Solution proposée

Un **serveur de licences centralisé** qui permet :
- ✅ Génération automatique de licences trial (30 jours)
- ✅ Validation des licences en ligne
- ✅ Révocation instantanée
- ✅ Statistiques d'utilisation
- ✅ Dashboard d'administration
- ✅ Fallback hors ligne si serveur inaccessible

---

## 🎯 Objectifs

### Phase 1 - MVP (Semaine 1)
- [x] API REST fonctionnelle
- [x] Endpoints trial + validation
- [x] Base de données PostgreSQL
- [x] Déploiement sur VPS OVH
- [x] HTTPS avec Let's Encrypt

### Phase 2 - Production (Semaine 2)
- [ ] Dashboard admin web
- [ ] Monitoring et logs
- [ ] Rate limiting
- [ ] Backup automatique BDD
- [ ] Documentation API

### Phase 3 - Avancé (Futur)
- [ ] Heartbeat / Analytics
- [ ] Notifications email
- [ ] Webhooks
- [ ] Multi-produits
- [ ] API pour partenaires

---

## 🏗️ Architecture Système

### Diagramme de haut niveau

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENTS (EasyFacture)                   │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Client 1    │  │  Client 2    │  │  Client N    │     │
│  │  (Windows)   │  │  (Windows)   │  │  (Windows)   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
          │  HTTPS          │  HTTPS          │  HTTPS
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────┐
│                   VPS OVH (Ubuntu 22.04)                    │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                    NGINX (Reverse Proxy)               │ │
│  │  - SSL/TLS (Let's Encrypt)                            │ │
│  │  - Rate Limiting                                       │ │
│  │  - Load Balancing                                      │ │
│  └────────────────────┬──────────────────────────────────┘ │
│                       │                                     │
│  ┌────────────────────▼──────────────────────────────────┐ │
│  │            FastAPI Application (Uvicorn)              │ │
│  │                                                        │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │  API Routes  │  │   Business   │  │   Security  │ │ │
│  │  │  /api/...    │  │     Logic    │  │   (JWT)     │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  └────────────────────┬──────────────────────────────────┘ │
│                       │                                     │
│  ┌────────────────────▼──────────────────────────────────┐ │
│  │              PostgreSQL Database                       │ │
│  │  - licenses table                                      │ │
│  │  - activations table                                   │ │
│  │  - heartbeats table (optionnel)                       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Stack technologique

**Backend**
- **Framework** : FastAPI 0.109.0
- **Serveur ASGI** : Uvicorn
- **ORM** : SQLAlchemy 2.0
- **Validation** : Pydantic V2
- **Auth** : JWT (python-jose)

**Base de données**
- **SGBD** : PostgreSQL 15
- **Migrations** : Alembic

**Déploiement**
- **Serveur** : VPS OVH Ubuntu 22.04
- **Reverse Proxy** : Nginx
- **SSL** : Let's Encrypt (Certbot)
- **Process Manager** : systemd
- **Monitoring** : (à définir - Prometheus/Grafana ?)

---

## 🔌 API REST

### Principes de conception

- **RESTful** : Respect des conventions HTTP
- **Versioning** : `/api/v1/...` pour compatibilité future
- **JSON** : Entrée/sortie en JSON
- **Stateless** : Pas de session côté serveur
- **Idempotent** : GET/PUT/DELETE sont idempotents
- **Rate limited** : Protection contre abus

### Endpoints

#### 1. Demande de licence Trial

```http
POST /api/v1/licenses/trial
Content-Type: application/json

{
  "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "email": "client@exemple.com",
  "product": "easyfacture",
  "version": "1.6.0"
}
```

**Réponse 201 Created**
```json
{
  "success": true,
  "license_key": "gAAAAABl...encrypted_license_data...",
  "license_type": "trial",
  "expires_at": "2026-01-30T23:59:59Z",
  "days_remaining": 30,
  "message": "Licence trial créée avec succès"
}
```

**Réponse 409 Conflict** (si déjà existe)
```json
{
  "success": false,
  "error": "TRIAL_ALREADY_EXISTS",
  "message": "Une licence trial existe déjà pour cette machine",
  "existing_license": {
    "expires_at": "2026-01-15T23:59:59Z",
    "days_remaining": 15
  }
}
```

**Réponse 429 Too Many Requests**
```json
{
  "success": false,
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Trop de requêtes. Réessayez dans 1 heure.",
  "retry_after": 3600
}
```

---

#### 2. Activation de licence payante

```http
POST /api/v1/licenses/activate
Content-Type: application/json

{
  "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "activation_code": "XXXX-XXXX-XXXX-XXXX",
  "email": "client@exemple.com"
}
```

**Réponse 200 OK**
```json
{
  "success": true,
  "license_key": "gAAAAABl...encrypted_license_data...",
  "license_type": "annual",
  "expires_at": "2026-12-31T23:59:59Z",
  "days_remaining": 365,
  "message": "Licence activée avec succès"
}
```

**Réponse 404 Not Found**
```json
{
  "success": false,
  "error": "INVALID_ACTIVATION_CODE",
  "message": "Code d'activation invalide ou déjà utilisé"
}
```

---

#### 3. Validation de licence

```http
POST /api/v1/licenses/validate
Content-Type: application/json

{
  "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "license_key": "gAAAAABl...encrypted_license_data..."
}
```

**Réponse 200 OK** (licence valide)
```json
{
  "success": true,
  "valid": true,
  "license_type": "annual",
  "expires_at": "2026-12-31T23:59:59Z",
  "days_remaining": 365,
  "is_active": true,
  "customer_email": "client@exemple.com"
}
```

**Réponse 200 OK** (licence expirée)
```json
{
  "success": true,
  "valid": false,
  "error": "LICENSE_EXPIRED",
  "message": "Votre licence a expiré le 2025-12-31",
  "expired_at": "2025-12-31T23:59:59Z",
  "renewal_url": "https://easyfacture.com/renew"
}
```

---

#### 4. Heartbeat (optionnel - Phase 2)

```http
POST /api/v1/licenses/heartbeat
Content-Type: application/json

{
  "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "license_key": "gAAAAABl...",
  "app_version": "1.6.0",
  "os_info": "Windows 11 Pro"
}
```

**Réponse 200 OK**
```json
{
  "success": true,
  "message": "Heartbeat enregistré",
  "last_check": "2025-12-31T12:00:00Z"
}
```

---

#### 5. Révocation de licence (Admin seulement)

```http
DELETE /api/v1/admin/licenses/{machine_id}
Authorization: Bearer <admin_jwt_token>
```

**Réponse 200 OK**
```json
{
  "success": true,
  "message": "Licence révoquée avec succès"
}
```

---

### Gestion des erreurs

Toutes les erreurs suivent ce format :

```json
{
  "success": false,
  "error": "ERROR_CODE",
  "message": "Message lisible pour l'utilisateur",
  "details": {
    "field": "Description de l'erreur"
  },
  "timestamp": "2025-12-31T12:00:00Z",
  "request_id": "uuid-v4"
}
```

**Codes d'erreur standardisés**
- `INVALID_REQUEST` : Requête malformée
- `MACHINE_ID_REQUIRED` : Machine ID manquant
- `INVALID_MACHINE_ID` : Format Machine ID invalide
- `LICENSE_NOT_FOUND` : Licence introuvable
- `LICENSE_EXPIRED` : Licence expirée
- `LICENSE_REVOKED` : Licence révoquée
- `TRIAL_ALREADY_EXISTS` : Trial déjà créé
- `RATE_LIMIT_EXCEEDED` : Trop de requêtes
- `SERVER_ERROR` : Erreur serveur interne

---

## 💾 Modèle de Données

### Schéma PostgreSQL

```sql
-- Table principale des licences
CREATE TABLE licenses (
    id SERIAL PRIMARY KEY,

    -- Identification
    machine_id VARCHAR(32) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    product VARCHAR(50) DEFAULT 'easyfacture',

    -- Licence
    license_key TEXT NOT NULL,
    license_type VARCHAR(20) NOT NULL, -- 'trial', 'monthly', 'annual', 'lifetime'
    activation_code VARCHAR(50) UNIQUE, -- Code pour activation payante

    -- Dates
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_validated_at TIMESTAMP,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_revoked BOOLEAN DEFAULT FALSE,
    revoked_at TIMESTAMP,
    revoked_reason TEXT,

    -- Métadonnées
    app_version VARCHAR(20),
    ip_address INET,
    user_agent TEXT,

    -- Indexes
    INDEX idx_machine_id (machine_id),
    INDEX idx_email (email),
    INDEX idx_activation_code (activation_code),
    INDEX idx_expires_at (expires_at),
    INDEX idx_is_active (is_active)
);

-- Historique des activations/validations
CREATE TABLE activations (
    id SERIAL PRIMARY KEY,
    license_id INTEGER REFERENCES licenses(id) ON DELETE CASCADE,

    -- Action
    action_type VARCHAR(20) NOT NULL, -- 'trial_created', 'activated', 'validated', 'heartbeat'

    -- Contexte
    ip_address INET,
    user_agent TEXT,
    app_version VARCHAR(20),
    os_info TEXT,

    -- Date
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_license_id (license_id),
    INDEX idx_action_type (action_type),
    INDEX idx_created_at (created_at)
);

-- Heartbeats (optionnel - Phase 2)
CREATE TABLE heartbeats (
    id SERIAL PRIMARY KEY,
    license_id INTEGER REFERENCES licenses(id) ON DELETE CASCADE,

    -- Informations
    app_version VARCHAR(20),
    os_info TEXT,
    ip_address INET,

    -- Date
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_license_id (license_id),
    INDEX idx_created_at (created_at)
);

-- Codes d'activation (pour licences payantes)
CREATE TABLE activation_codes (
    id SERIAL PRIMARY KEY,

    -- Code
    code VARCHAR(50) UNIQUE NOT NULL,

    -- Type de licence
    license_type VARCHAR(20) NOT NULL,
    duration_days INTEGER NOT NULL,

    -- Status
    is_used BOOLEAN DEFAULT FALSE,
    used_by_license_id INTEGER REFERENCES licenses(id),
    used_at TIMESTAMP,

    -- Dates
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP, -- Le code lui-même peut expirer

    -- Métadonnées
    created_by VARCHAR(100), -- Admin qui a créé le code
    notes TEXT,

    -- Indexes
    INDEX idx_code (code),
    INDEX idx_is_used (is_used)
);
```

### Relations

```
licenses (1) ──< (N) activations
licenses (1) ──< (N) heartbeats
licenses (N) ──> (1) activation_codes (optionnel)
```

---

## 🔒 Sécurité

### 1. Transport (HTTPS)

- ✅ **Obligatoire** : Toutes les requêtes en HTTPS
- ✅ Let's Encrypt pour certificat SSL gratuit
- ✅ HSTS activé (Strict-Transport-Security)
- ✅ Redirection HTTP → HTTPS automatique

### 2. Authentification

**API publique** (trial, validation)
- Pas d'auth requise
- Rate limiting strict

**API admin** (révocation, stats)
- JWT Bearer token
- Expiration 1 heure
- Refresh token (7 jours)

### 3. Rate Limiting

```python
# Limites par IP
/api/v1/licenses/trial      → 3 requêtes / heure / IP
/api/v1/licenses/activate   → 10 requêtes / heure / IP
/api/v1/licenses/validate   → 100 requêtes / heure / IP
/api/v1/licenses/heartbeat  → 1 requête / 24h / machine_id
```

### 4. Validation des données

- ✅ Pydantic pour validation stricte
- ✅ Machine ID : exactement 32 caractères hexadécimaux
- ✅ Email : format RFC 5322
- ✅ Sanitisation des entrées

### 5. Secrets

```bash
# .env sur le serveur
DATABASE_URL=postgresql://user:password@localhost/licenses
SECRET_KEY=...64_caracteres_random...
JWT_SECRET=...64_caracteres_random...
ENCRYPTION_KEY=...fernet_key...
```

### 6. Protection contre attaques

- ✅ SQL Injection : ORM SQLAlchemy
- ✅ XSS : Pas de HTML généré
- ✅ CSRF : API stateless, pas de cookies
- ✅ DDoS : Rate limiting + Cloudflare (optionnel)

---

## 🚀 Déploiement

### Architecture VPS

```
VPS OVH (Ubuntu 22.04)
├── /opt/license-server/
│   ├── venv/
│   ├── app/
│   ├── main.py
│   └── .env
├── /etc/nginx/sites-available/license-server
├── /etc/systemd/system/license-server.service
└── /var/log/license-server/
```

### Stack de déploiement

1. **PostgreSQL** : Port 5432 (local seulement)
2. **Uvicorn** : Port 8000 (local seulement)
3. **Nginx** : Port 80 (redirect) + 443 (HTTPS)
4. **Certbot** : Auto-renouvellement SSL

### Commandes de déploiement

```bash
# Installation initiale
git clone https://github.com/adoudi-mondher/license-server.git /opt/license-server
cd /opt/license-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configuration
cp .env.example .env
# Éditer .env avec vraies valeurs

# Base de données
alembic upgrade head

# Service systemd
sudo cp license-server.service /etc/systemd/system/
sudo systemctl enable license-server
sudo systemctl start license-server

# Nginx
sudo cp nginx.conf /etc/nginx/sites-available/license-server
sudo ln -s /etc/nginx/sites-available/license-server /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# SSL
sudo certbot --nginx -d licenses.votre-domaine.com
```

---

## 📈 Roadmap

### Phase 1 - MVP (Semaine 1) ✅
- API REST fonctionnelle
- Trial + Validation + Activation
- PostgreSQL setup
- Déploiement VPS

### Phase 2 - Production (Semaine 2)
- Dashboard admin (Flask-Admin ou React)
- Monitoring (logs, métriques)
- Backup automatique BDD
- Documentation Swagger

### Phase 3 - Analytics (Mois 1)
- Heartbeat system
- Statistiques d'usage
- Graphiques dans dashboard
- Export CSV

### Phase 4 - Avancé (Futur)
- Multi-produits
- Webhooks pour événements
- API pour partenaires
- Notifications email automatiques
- Auto-update du client

---

## 📚 Ressources

- **FastAPI Docs** : https://fastapi.tiangolo.com
- **SQLAlchemy** : https://docs.sqlalchemy.org
- **PostgreSQL** : https://www.postgresql.org/docs/
- **Let's Encrypt** : https://letsencrypt.org/docs/

---

**Next Steps** : Valider cette architecture avant de commencer le code ! 🚀
