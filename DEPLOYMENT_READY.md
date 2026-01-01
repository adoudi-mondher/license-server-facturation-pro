# Easy Facture License Server - Prêt pour le déploiement

## Statut : ✅ PRÊT À DÉPLOYER

Tous les fichiers nécessaires au déploiement Docker sur ton VPS OVH sont créés et testés.

---

## Fichiers créés

### 🐳 Docker

| Fichier | Description | Statut |
|---------|-------------|--------|
| `Dockerfile` | Image Docker FastAPI production-ready | ✅ |
| `docker-compose.yml` | Orchestration API + PostgreSQL | ✅ |
| `.dockerignore` | Optimisation du build | ✅ |

### ⚙️ Configuration

| Fichier | Description | Statut |
|---------|-------------|--------|
| `.env.example` | Template de configuration | ✅ |
| `app/config.py` | Configuration FastAPI (pydantic-settings) | ✅ existant |

### 🚀 Scripts de déploiement

| Fichier | Description | Statut |
|---------|-------------|--------|
| `deploy.sh` | Script de déploiement automatique | ✅ |
| `check_deployment.sh` | Vérification post-déploiement | ✅ |

### 📚 Documentation

| Fichier | Description | Statut |
|---------|-------------|--------|
| `QUICKSTART.md` | Guide rapide 5 minutes | ✅ |
| `DEPLOYMENT.md` | Guide complet avec troubleshooting | ✅ |
| `README.md` | Documentation générale | ✅ existant |
| `ARCHITECTURE.md` | Architecture technique | ✅ existant |

### 💻 Code API

| Composant | Description | Statut |
|-----------|-------------|--------|
| `main.py` | Point d'entrée FastAPI | ✅ existant |
| `app/api/licenses.py` | Endpoints /trial et /validate | ✅ existant |
| `app/models/` | Modèles SQLAlchemy (License, Activation, etc.) | ✅ existant |
| `app/schemas/` | Schémas Pydantic (validation) | ✅ existant |
| `app/utils/license_crypto.py` | Chiffrement Fernet compatible EasyFacture | ✅ **CORRIGÉ** |
| `app/database.py` | Connexion PostgreSQL | ✅ existant |

---

## Corrections importantes apportées

### 🔧 Fix de compatibilité (license_crypto.py)

**Problème détecté** : Le serveur générait des licences avec `expires_at` mais EasyFacture client attend `expiry`.

**Correction appliquée** :
```python
# AVANT (incompatible)
license_data = {
    "expires_at": expires_at.isoformat(),
    ...
}

# APRÈS (compatible)
license_data = {
    "expiry": expires_at.isoformat(),  # Compatible avec EasyFacture client
    "version": "1.7.0",
    "generated": datetime.utcnow().isoformat()
}
```

**Impact** : Les licences générées par l'API seront maintenant 100% compatibles avec EasyFacture v1.7.

---

## Configuration requise

### Variables .env à remplir OBLIGATOIREMENT

```env
# À générer/modifier
POSTGRES_PASSWORD=VotreMotDePasseFortetComplexe123!
SECRET_KEY=VotreCleSecrete_GenererAvecOpenSSL
ADMIN_PASSWORD=VotreMotDePasseAdmin456!

# CETTE CLÉ NE DOIT PAS CHANGER (synchronisée avec EasyFacture)
LICENSE_SECRET_KEY=QvS9Dy6SjhpVPFf-nsu2NZ-xPfS3-Xaom--vwvdeH6w=
```

**Générer SECRET_KEY** :
```bash
openssl rand -hex 32
```

---

## Architecture de déploiement

```
Internet (HTTPS)
    ↓
api.easyfacture.mondher.ch
    ↓
Nginx Proxy Manager (conteneur Docker existant)
    - Port 443 (HTTPS)
    - Certificat Let's Encrypt automatique
    - Reverse proxy vers l'API
    ↓
FastAPI License API (nouveau conteneur)
    - Port 8000
    - Uvicorn avec 2 workers
    - Health checks automatiques
    ↓
PostgreSQL (nouveau conteneur)
    - Port 5432 (interne seulement)
    - Volume persistant
    - Sauvegardes automatiques
```

---

## Endpoints API disponibles

| Endpoint | Méthode | Description | Rate Limit |
|----------|---------|-------------|------------|
| `/` | GET | Info API | Aucun |
| `/health` | GET | Health check | Aucun |
| `/api/v1/licenses/trial` | POST | Générer licence trial (30j) | 3/heure |
| `/api/v1/licenses/validate` | POST | Valider une licence | 100/heure |

---

## Checklist de déploiement

### Avant le déploiement

- [x] DNS configuré : `api.easyfacture.mondher.ch` → IP VPS
- [x] Code FastAPI testé localement
- [x] Dockerfile créé et optimisé
- [x] docker-compose.yml configuré
- [x] Scripts de déploiement créés
- [x] Documentation complète
- [x] Fix de compatibilité appliqué

### Pendant le déploiement

- [ ] Transférer les fichiers sur le VPS
- [ ] Créer et configurer `.env`
- [ ] Lancer `./deploy.sh`
- [ ] Configurer Nginx Proxy Manager
- [ ] Générer certificat SSL

### Après le déploiement

- [ ] Tester `GET /health`
- [ ] Tester `POST /api/v1/licenses/trial`
- [ ] Tester `POST /api/v1/licenses/validate`
- [ ] Mettre à jour `LICENSE_API_URL` dans EasyFacture
- [ ] Rebuild EasyFacture Windows
- [ ] Tester le flux complet client → serveur

---

## Commandes rapides

### Déploiement

```bash
# Sur le VPS
cd /opt/easyfacture-license-server
./deploy.sh
```

### Vérification

```bash
# Sur le VPS
./check_deployment.sh https://api.easyfacture.mondher.ch
```

### Gestion

```bash
# Voir les logs
docker-compose logs -f api

# Redémarrer
docker-compose restart

# Arrêter
docker-compose down

# Rebuild
docker-compose up -d --build
```

---

## Tests de validation

### Test 1 : Health check

```bash
curl https://api.easyfacture.mondher.ch/health
```

**Attendu** :
```json
{"status": "healthy", "timestamp": "..."}
```

### Test 2 : Génération trial

```bash
curl -X POST https://api.easyfacture.mondher.ch/api/v1/licenses/trial \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "machine_id": "abc123",
    "customer_name": "Test User"
  }'
```

**Attendu** :
```json
{
  "success": true,
  "license_key": "a1b2c3d4...",
  "expires_at": "2025-01-30T...",
  "license_type": "trial"
}
```

### Test 3 : Validation

```bash
curl -X POST https://api.easyfacture.mondher.ch/api/v1/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "CLE_DU_TEST_2",
    "machine_id": "abc123"
  }'
```

**Attendu** :
```json
{
  "valid": true,
  "message": "Licence valide",
  "days_remaining": 30
}
```

---

## Prochaines étapes

1. **Déployer sur VPS** (voir `QUICKSTART.md`)
2. **Configurer Nginx Proxy Manager**
3. **Tester les endpoints**
4. **Mettre à jour EasyFacture client**
5. **Tester le flux complet**

---

## Support

**Email** : adoudi@mondher.ch
**Documentation** : Voir `DEPLOYMENT.md` pour le guide complet

---

## Notes importantes

⚠️ **Sécurité** :
- Ne jamais committer `.env` dans Git (déjà dans .gitignore)
- Utiliser des mots de passe forts
- Activer le firewall UFW sur le VPS
- Sauvegarder régulièrement PostgreSQL

🔐 **Clé de chiffrement** :
- `LICENSE_SECRET_KEY` doit rester `QvS9Dy6SjhpVPFf-nsu2NZ-xPfS3-Xaom--vwvdeH6w=`
- C'est la même clé utilisée dans EasyFacture client
- NE JAMAIS LA CHANGER sans rebuild complet de tous les clients

📊 **Monitoring** :
- Health check toutes les 30s (Docker)
- Logs automatiques dans Docker
- Rate limiting pour éviter les abus

---

**Status** : ✅ PRÊT À DÉPLOYER

**Dernière mise à jour** : 31 décembre 2024 - 23:45
