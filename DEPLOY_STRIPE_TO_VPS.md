# Guide de déploiement - Stripe Lifetime License

**Date**: 2026-01-04
**Version**: 2.0
**Objectif**: Déployer la fonctionnalité Stripe pour licences Lifetime sur VPS OVH

---

## 📋 Prérequis

- [x] VPS OVH accessible (51.38.185.148)
- [x] License-server v1.0 (trial) déjà déployé et fonctionnel
- [x] Code v2.0 avec Stripe prêt localement
- [ ] Compte Stripe configuré
- [ ] Webhook Stripe configuré

---

## 🚀 Étapes de déploiement

### 1. Se connecter au VPS

```bash
ssh root@51.38.185.148
```

### 2. Aller dans le dossier license-server

```bash
cd /root/license-server  # ou le chemin où il est installé
```

### 3. Sauvegarder la version actuelle

```bash
# Créer un backup
cp -r /root/license-server /root/license-server_backup_$(date +%Y%m%d)

# Vérifier le backup
ls -la /root/license-server_backup_*
```

### 4. Mettre à jour le code depuis Git

```bash
# Vérifier la branche
git branch

# Récupérer les derniers changements
git pull origin main

# Vérifier les fichiers modifiés
git log --oneline -5
```

**Fichiers attendus dans le pull:**
- `app/api/payment.py` (nouveau)
- `app/models/license.py` (modifié - colonnes Stripe)
- `app/schemas/license.py` (modifié - nouveaux schémas)
- `main.py` (modifié - import payment_router)
- `requirements.txt` (modifié - ajout stripe)
- `.env.example` (modifié - variables Stripe)

### 5. Installer la dépendance Stripe

```bash
# Option 1: Dans le conteneur Docker (recommandé)
docker-compose exec api pip install stripe==8.0.0

# Option 2: Rebuilder l'image
docker-compose down
docker-compose build --no-cache api
docker-compose up -d
```

### 6. Configurer les variables Stripe dans .env

```bash
# Éditer le fichier .env
nano .env
```

**Ajouter à la fin du fichier:**

```bash
# ==============================================
# STRIPE PAYMENT (Licences Lifetime)
# ==============================================
# Clés API Stripe
STRIPE_SECRET_KEY=sk_test_XXXXXX  # À remplacer par la vraie clé
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXX

# Webhook secret (configurer après étape 9)
STRIPE_WEBHOOK_SECRET=whsec_XXXXXX

# Price IDs (créer dans Stripe Dashboard)
STRIPE_PRICE_EUR=price_XXXXXX_EUR  # Prix 199€

# URLs de redirection
STRIPE_SUCCESS_URL=https://easyfacture.mondher.ch/payment/success?session_id={CHECKOUT_SESSION_ID}
STRIPE_CANCEL_URL=https://easyfacture.mondher.ch/payment/cancel
```

**Sauvegarder:** `Ctrl+O` puis `Ctrl+X`

### 7. Migrer la base de données PostgreSQL

```bash
# Entrer dans le conteneur PostgreSQL
docker-compose exec postgres psql -U licenseuser -d easyfacture_licenses
```

**Exécuter les migrations SQL:**

```sql
-- Ajouter les colonnes Stripe au modèle License
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS stripe_session_id VARCHAR(255);
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255);
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS amount_paid INTEGER;
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'EUR';

-- Créer les index pour performance
CREATE INDEX IF NOT EXISTS idx_licenses_stripe_customer ON licenses(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_licenses_stripe_session ON licenses(stripe_session_id);
CREATE INDEX IF NOT EXISTS idx_licenses_stripe_payment ON licenses(stripe_payment_intent_id);

-- Vérifier que les colonnes ont été ajoutées
\d licenses

-- Quitter PostgreSQL
\q
```

**Attendu:** Vous devez voir les nouvelles colonnes dans la description de la table.

### 8. Redémarrer l'API

```bash
# Redémarrer le conteneur API
docker-compose restart api

# Vérifier les logs
docker-compose logs -f api
```

**Logs attendus:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Appuyez sur Ctrl+C pour quitter les logs**

### 9. Tester l'API en mode test Stripe

```bash
# Test 1: Vérifier que l'endpoint existe
curl http://localhost:8000/api/create-checkout-session \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"machine_id":"test123","email":"test@mondher.ch","currency":"eur"}'
```

**Réponse attendue (avec Stripe test):**
```json
{
  "success": true,
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_..."
}
```

**OU (si price_id pas configuré):**
```json
{
  "detail": "Configuration Stripe manquante pour la devise EUR"
}
```

### 10. Configurer Stripe Dashboard

**Aller sur:** https://dashboard.stripe.com

#### 10.1 Créer le produit

1. **Products** → **Add product**
2. Nom: `Easy Facture - Licence Lifetime`
3. Description: `Licence à vie pour Easy Facture - Application de facturation professionnelle`

#### 10.2 Créer le prix EUR

1. Dans le produit, cliquer **Add another price**
2. Type: `One-time`
3. Montant: `199.00 EUR`
4. Cliquer **Add price**
5. **Copier le Price ID:** `price_XXXXXXEUR` (commence par `price_`)

#### 10.3 Mettre à jour .env avec le Price ID

```bash
# Sur le VPS
nano .env

# Modifier:
STRIPE_PRICE_EUR=price_1XXXXXXEUR  # Remplacer par le vrai ID

# Sauvegarder: Ctrl+O puis Ctrl+X

# Redémarrer l'API
docker-compose restart api
```

### 11. Configurer le Webhook Stripe

1. **Stripe Dashboard** → **Developers** → **Webhooks**
2. Cliquer **Add endpoint**
3. **Endpoint URL:** `https://api.easyfacture.mondher.ch/stripe/webhook`
4. **Events to send:**
   - Sélectionner `checkout.session.completed`
5. Cliquer **Add endpoint**
6. **Copier le Signing secret:** `whsec_XXXXXX`

```bash
# Sur le VPS
nano .env

# Modifier:
STRIPE_WEBHOOK_SECRET=whsec_XXXXXX  # Remplacer par le vrai secret

# Sauvegarder: Ctrl+O puis Ctrl+X

# Redémarrer l'API
docker-compose restart api
```

### 12. Test complet du flux Stripe

```bash
# Depuis votre machine locale
curl -X POST https://api.easyfacture.mondher.ch/api/create-checkout-session \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "test_deploy_machine_id_123",
    "email": "mondher@mondher.ch",
    "currency": "eur"
  }'
```

**Réponse attendue:**
```json
{
  "success": true,
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_..."
}
```

**Ouvrir `checkout_url` dans le navigateur:**
1. Utiliser carte test: `4242 4242 4242 4242`
2. Date: n'importe quelle date future
3. CVC: n'importe quel 3 chiffres
4. Cliquer **Pay**

**Vérifier dans la BDD:**
```bash
# Sur le VPS
docker-compose exec postgres psql -U licenseuser -d easyfacture_licenses -c \
  "SELECT machine_id, license_type, stripe_payment_intent_id, amount_paid, currency
   FROM licenses
   WHERE machine_id = 'test_deploy_machine_id_123';"
```

**Attendu:**
```
     machine_id           | license_type | stripe_payment_intent_id | amount_paid | currency
--------------------------+--------------+--------------------------+-------------+----------
 test_deploy_machine_id_123 | lifetime     | pi_XXXXXXXXXX            |       19900 | EUR
```

---

## ✅ Checklist finale

- [ ] Code v2.0 pullé depuis Git
- [ ] Dépendance `stripe==8.0.0` installée
- [ ] Variables Stripe configurées dans `.env`
- [ ] Migration BDD appliquée (colonnes Stripe)
- [ ] API redémarrée sans erreurs
- [ ] Produit créé dans Stripe Dashboard
- [ ] Prix EUR créé (price_XXXXXXEUR)
- [ ] Webhook configuré (whsec_XXXXXX)
- [ ] Test création session réussi
- [ ] Test paiement Stripe test réussi
- [ ] Vérification BDD: licence lifetime créée

---

## 🔧 Troubleshooting

### Erreur: "Configuration Stripe manquante"

**Cause:** Price ID non configuré ou invalide

**Solution:**
```bash
# Vérifier .env
grep STRIPE_PRICE .env

# S'assurer que c'est un vrai price_id depuis Stripe Dashboard
STRIPE_PRICE_EUR=price_1XXXXXXEUR  # Doit commencer par "price_"
```

### Erreur: "Invalid signature" sur webhook

**Cause:** `STRIPE_WEBHOOK_SECRET` incorrect

**Solution:**
1. Aller dans Stripe Dashboard → Webhooks
2. Cliquer sur votre endpoint
3. Copier le "Signing secret" (whsec_...)
4. Mettre à jour `.env` et redémarrer

### Webhook non appelé après paiement

**Vérifier:**
1. Logs API: `docker-compose logs -f api`
2. Logs Stripe Dashboard: https://dashboard.stripe.com/test/logs
3. URL webhook correcte: `https://api.easyfacture.mondher.ch/stripe/webhook`

---

## 📊 Monitoring post-déploiement

```bash
# Voir logs en temps réel
docker-compose logs -f api

# Rechercher erreurs Stripe
docker-compose logs api | grep "Stripe"

# Voir toutes les licences lifetime créées
docker-compose exec postgres psql -U licenseuser -d easyfacture_licenses -c \
  "SELECT email, machine_id, license_type, amount_paid, created_at
   FROM licenses
   WHERE license_type = 'lifetime'
   ORDER BY created_at DESC
   LIMIT 10;"
```

---

**Créé le:** 2026-01-04
**Par:** Claude & Mondher
**Version:** 2.0 - Déploiement Stripe Production
