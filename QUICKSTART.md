# Easy Facture License Server - Démarrage rapide

Guide ultra-rapide pour déployer l'API sur ton VPS OVH.

## Ce que tu as besoin

1. **DNS configuré** : `api.easyfacture.mondher.ch` → IP de ton VPS ✅ (fait)
2. **Accès SSH** au VPS
3. **5-10 minutes**

## Étapes de déploiement

### 1. Transférer les fichiers sur le VPS

Depuis ta machine Windows (Git Bash ou PowerShell) :

```bash
# Avec SCP
scp -r d:/workflow/python/license-server root@TON-IP-VPS:/opt/easyfacture-license-server

# OU utiliser WinSCP / FileZilla
```

### 2. Se connecter au VPS

```bash
ssh root@TON-IP-VPS
cd /opt/easyfacture-license-server
```

### 3. Configurer les variables

```bash
# Copier l'exemple
cp .env.example .env

# Éditer le fichier
nano .env
```

**Modifier ces 3 valeurs OBLIGATOIRES** :

```env
POSTGRES_PASSWORD=MotDePasseFortetComplexe123!
SECRET_KEY=VotreCleSecrete_GenererAvecOpenSSL
ADMIN_PASSWORD=MotDePasseAdmin456!
```

**Générer SECRET_KEY** :
```bash
openssl rand -hex 32
```

**IMPORTANT** : La clé `LICENSE_SECRET_KEY` est déjà configurée et doit rester :
```env
LICENSE_SECRET_KEY=QvS9Dy6SjhpVPFf-nsu2NZ-xPfS3-Xaom--vwvdeH6w=
```

### 4. Lancer le déploiement

```bash
# Rendre le script exécutable
chmod +x deploy.sh

# Lancer
./deploy.sh
```

Le script va :
- ✅ Vérifier Docker et Docker Compose
- ✅ Builder les images
- ✅ Démarrer PostgreSQL
- ✅ Démarrer l'API FastAPI
- ✅ Vérifier que tout fonctionne

### 5. Configurer Nginx Proxy Manager

1. **Ouvrir** : `http://TON-IP-VPS:81`
2. **Login** : admin@example.com / changeme (puis changer)
3. **Ajouter Proxy Host** :

| Champ | Valeur |
|-------|--------|
| Domain Names | `api.easyfacture.mondher.ch` |
| Scheme | `http` |
| Forward Hostname | `easyfacture-license-api` |
| Forward Port | `8000` |
| Cache Assets | ✅ |
| Block Common Exploits | ✅ |
| Websockets Support | ❌ |

4. **Onglet SSL** :
   - Request a new SSL Certificate ✅
   - Force SSL ✅
   - Email : `adoudi@mondher.ch`
   - Agree to Let's Encrypt Terms ✅

5. **Save**

Nginx va automatiquement générer le certificat SSL (2-3 minutes).

### 6. Tester

```bash
# Test santé
curl https://api.easyfacture.mondher.ch/health

# Test génération trial
curl -X POST https://api.easyfacture.mondher.ch/api/v1/licenses/trial \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "machine_id": "abc123",
    "customer_name": "Test"
  }'
```

**Si tu vois une réponse JSON avec `"success": true`** → ✅ C'est bon !

### 7. Mettre à jour EasyFacture

Dans `facturation-app/config.py` :

```python
LICENSE_API_URL = 'https://api.easyfacture.mondher.ch/api/v1'
```

Rebuild l'application :

```bash
cd facturation-app/packaging/windows
bash build.sh
```

---

## Commandes utiles

```bash
# Voir les logs
docker-compose logs -f api

# Redémarrer
docker-compose restart

# Arrêter
docker-compose down

# Redémarrer après modification
docker-compose up -d --build

# Vérifier l'état
./check_deployment.sh https://api.easyfacture.mondher.ch
```

---

## Structure des fichiers déployés

```
/opt/easyfacture-license-server/
├── app/                    # Code FastAPI
├── main.py                 # Point d'entrée
├── Dockerfile              # Image Docker API
├── docker-compose.yml      # Orchestration
├── .env                    # Configuration (SECRET!)
├── deploy.sh               # Script de déploiement
└── check_deployment.sh     # Script de vérification
```

---

## En cas de problème

### L'API ne démarre pas

```bash
docker-compose logs -f api
```

### Certificat SSL non généré

1. Vérifier DNS : `nslookup api.easyfacture.mondher.ch`
2. Attendre 5-10 minutes (propagation)
3. Vérifier ports 80/443 ouverts : `ufw status`

### Erreur de connexion PostgreSQL

```bash
# Vérifier PostgreSQL
docker-compose logs -f postgres

# Redémarrer tout
docker-compose down && docker-compose up -d
```

---

## C'est tout ! 🎉

L'API est maintenant accessible sur **https://api.easyfacture.mondher.ch**

**Endpoints actifs :**
- `GET /health` - Health check
- `POST /api/v1/licenses/trial` - Générer licence trial
- `POST /api/v1/licenses/validate` - Valider licence

**Documentation complète** : [DEPLOYMENT.md](DEPLOYMENT.md)
