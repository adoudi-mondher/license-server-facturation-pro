# 🚀 Quick Start - License Server

Guide rapide pour démarrer le serveur de licences en 5 minutes.

---

## 📦 Installation Express

```bash
# 1. Cloner le projet
cd /d/workflow/python/license-server

# 2. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Créer la base de données PostgreSQL
createdb license_db

# 5. Configurer l'environnement
cp .env.example .env
```

---

## ⚙️ Configuration Minimale

Éditez `.env` avec ces valeurs essentielles:

```bash
# Database (adapter selon votre config PostgreSQL)
DATABASE_URL=postgresql://postgres:password@localhost:5432/license_db

# Générer avec: openssl rand -hex 32
SECRET_KEY=a64f54567a183d8f31bca41e5454275ea772c6c8c3c4e1abb1b5ed65749fca80

# IMPORTANT: Utiliser la MÊME clé que dans EasyFacture/generate_customer_license.py
LICENSE_SECRET_KEY=votre-cle-existante-easyfacture

# Autres (valeurs par défaut OK)
ENVIRONMENT=development
DEFAULT_TRIAL_DAYS=30
```

---

## 🎯 Lancer le serveur

```bash
python main.py
```

Ou:
```bash
uvicorn main:app --reload
```

**Serveur démarré sur**: http://127.0.0.1:8000

**Documentation interactive**: http://127.0.0.1:8000/docs

---

## 🧪 Test rapide

### 1. Demander une licence trial

```bash
curl -X POST http://127.0.0.1:8000/api/v1/licenses/trial \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    "customer_name": "Test User"
  }'
```

**Réponse attendue**:
```json
{
  "success": true,
  "message": "Licence d'essai générée avec succès",
  "license_key": "gAAAAABk...",
  "expires_at": "2025-02-15T10:30:00",
  "license_type": "trial"
}
```

### 2. Valider la licence

```bash
curl -X POST http://127.0.0.1:8000/api/v1/licenses/validate \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "gAAAAABk...",
    "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
  }'
```

**Réponse attendue**:
```json
{
  "valid": true,
  "message": "Licence valide",
  "expires_at": "2025-02-15T10:30:00",
  "days_remaining": 25,
  "license_type": "trial"
}
```

---

## ✅ Checklist

- [ ] PostgreSQL installé et démarré
- [ ] Base `license_db` créée
- [ ] Environnement virtuel activé
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] Fichier `.env` configuré avec `DATABASE_URL` et `LICENSE_SECRET_KEY`
- [ ] Serveur démarre sans erreur (`python main.py`)
- [ ] Swagger UI accessible (http://127.0.0.1:8000/docs)
- [ ] Test trial réussi
- [ ] Test validation réussi

---

## 🔧 Problèmes courants

### "ModuleNotFoundError: No module named 'app'"

**Solution**: Activez l'environnement virtuel
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### "connection to server failed"

**Solution**: Vérifiez que PostgreSQL est démarré
```bash
# Linux
sudo systemctl start postgresql

# macOS
brew services start postgresql

# Windows
# Démarrer le service PostgreSQL via Services
```

### "FATAL: database 'license_db' does not exist"

**Solution**: Créez la base
```bash
createdb license_db
# ou
psql -U postgres -c "CREATE DATABASE license_db;"
```

### "Invalid license key" lors du test

**Solution**: Vérifiez que `LICENSE_SECRET_KEY` dans `.env` est identique à celle utilisée dans EasyFacture

---

## 📚 Prochaines étapes

1. Lire [ARCHITECTURE.md](ARCHITECTURE.md) pour comprendre la conception
2. Lire [README.md](README.md) pour la documentation complète
3. Tester tous les endpoints via Swagger UI
4. Intégrer l'API dans EasyFacture client
5. Déployer sur VPS (voir README.md section Déploiement)

---

**Prêt à coder !** 🎉
