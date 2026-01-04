# Intégration Stripe - License Server

Guide complet pour l'intégration des paiements Stripe pour les licences lifetime Easy Facture.

**Date**: 2026-01-03
**Version**: 1.0
**Status**: ✅ Implémentation backend complète

---

## 📋 Table des matières

1. [Modifications apportées](#modifications-apportées)
2. [Configuration requise](#configuration-requise)
3. [Installation et déploiement](#installation-et-déploiement)
4. [API Endpoints](#api-endpoints)
5. [Tests](#tests)
6. [Sécurité](#sécurité)

---

## Modifications apportées

### 1. Modèle `License` (app/models/license.py)

**Nouvelles colonnes ajoutées:**
```python
# Stripe Payment Information
stripe_customer_id = Column(String(255), nullable=True, index=True)
stripe_session_id = Column(String(255), nullable=True, index=True)
stripe_payment_intent_id = Column(String(255), nullable=True, index=True)
amount_paid = Column(Integer, nullable=True)  # Montant en centimes
currency = Column(String(3), default='EUR', nullable=True)
```

**Migration BDD requise:**
```sql
ALTER TABLE licenses ADD COLUMN stripe_customer_id VARCHAR(255);
ALTER TABLE licenses ADD COLUMN stripe_session_id VARCHAR(255);
ALTER TABLE licenses ADD COLUMN stripe_payment_intent_id VARCHAR(255);
ALTER TABLE licenses ADD COLUMN amount_paid INTEGER;
ALTER TABLE licenses ADD COLUMN currency VARCHAR(3) DEFAULT 'EUR';

CREATE INDEX idx_licenses_stripe_customer ON licenses(stripe_customer_id);
CREATE INDEX idx_licenses_stripe_session ON licenses(stripe_session_id);
CREATE INDEX idx_licenses_stripe_payment ON licenses(stripe_payment_intent_id);
```

### 2. Schémas Pydantic (app/schemas/license.py)

**Nouveaux schémas:**
- `CreateCheckoutSessionRequest` - Création session Stripe
- `CheckoutSessionResponse` - Réponse avec URL checkout
- `StripeWebhookEvent` - Événement webhook Stripe

### 3. Routes Payment (app/api/payment.py)

**Nouveau fichier créé** avec 2 endpoints:

#### `POST /api/create-checkout-session`
Crée une session Stripe Checkout pour acheter une licence lifetime.

**Request:**
```json
{
  "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "email": "user@example.com",
  "currency": "eur"
}
```

**Response:**
```json
{
  "success": true,
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_..."
}
```

**Rate limit**: 10 requêtes/heure par IP

#### `POST /stripe/webhook`
Webhook Stripe pour activer les licences après paiement réussi.

**Événements traités:**
- `checkout.session.completed` → Active la licence lifetime

**Sécurité:**
- Vérification obligatoire de la signature Stripe
- Idempotence (ne traite pas 2 fois le même paiement)

### 4. Main.py

**Modifications:**
```python
from app.api.payment import router as payment_router

app.include_router(payment_router)
```

### 5. Requirements.txt

**Nouvelle dépendance:**
```
stripe==8.0.0
```

---

## Configuration requise

### Variables d'environnement (.env)

Ajouter dans le fichier `.env` du license-server:

```bash
# ==============================================
# STRIPE PAYMENT
# ==============================================
# Clés API Stripe
STRIPE_SECRET_KEY=sk_test_XXXXXX  # sk_live_XXXXXX en production
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXX

# Price IDs (créés dans Stripe Dashboard)
STRIPE_PRICE_EUR=price_1XXXXXXEUR
STRIPE_PRICE_USD=price_1XXXXXXUSD
STRIPE_PRICE_CHF=price_1XXXXXXCHF
STRIPE_PRICE_GBP=price_1XXXXXXGBP

# URLs de redirection
STRIPE_SUCCESS_URL=https://easyfacture.mondher.ch/payment/success?session_id={CHECKOUT_SESSION_ID}
STRIPE_CANCEL_URL=https://easyfacture.mondher.ch/payment/cancel
```

### Configuration Stripe Dashboard

1. **Créer le produit** "Easy Facture - Licence Lifetime"
2. **Créer les prix** pour chaque devise:
   - EUR: 199.00€ (one-time payment)
   - USD: 219.00$ (one-time payment)
   - CHF: 199.00 CHF (one-time payment)
   - GBP: 179.00£ (one-time payment)

3. **Configurer le webhook**:
   - URL: `https://api.easyfacture.mondher.ch/stripe/webhook`
   - Événements: `checkout.session.completed`
   - Récupérer le `whsec_XXXXXX` secret

---

## Installation et déploiement

### 1. En local (développement)

```bash
cd license-server

# Installer stripe
pip install stripe==8.0.0

# Ou réinstaller toutes les dépendances
pip install -r requirements.txt

# Ajouter les variables Stripe dans .env
nano .env

# Appliquer la migration BDD
# Option 1: Automatique (SQLAlchemy)
python -c "from app.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"

# Option 2: Manuelle (SQL)
psql -U licenseuser -d easyfacture_licenses < migration_stripe.sql

# Redémarrer le serveur
uvicorn main:app --reload
```

### 2. En production (VPS OVH)

```bash
# Se connecter au VPS
ssh root@51.38.185.148

# Aller dans le dossier license-server
cd /root/license-server

# Mettre à jour le code
git pull origin main

# Installer stripe dans le conteneur Docker
docker-compose exec api pip install stripe==8.0.0

# Ou rebuilder l'image
docker-compose down
docker-compose up -d --build

# Vérifier les logs
docker-compose logs -f api

# Appliquer la migration BDD
docker-compose exec postgres psql -U licenseuser -d easyfacture_licenses
```

**Migration SQL à exécuter dans PostgreSQL:**
```sql
-- Dans le conteneur postgres
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS stripe_session_id VARCHAR(255);
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255);
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS amount_paid INTEGER;
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'EUR';

CREATE INDEX IF NOT EXISTS idx_licenses_stripe_customer ON licenses(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_licenses_stripe_session ON licenses(stripe_session_id);
CREATE INDEX IF NOT EXISTS idx_licenses_stripe_payment ON licenses(stripe_payment_intent_id);

-- Vérifier
\d licenses
```

---

## API Endpoints

### Créer une session de paiement

**Endpoint:** `POST /api/create-checkout-session`

**cURL:**
```bash
curl -X POST https://api.easyfacture.mondher.ch/api/create-checkout-session \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "test123abc456def",
    "email": "test@example.com",
    "currency": "eur"
  }'
```

**Response (succès):**
```json
{
  "success": true,
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_a1b2c3...",
  "session_id": "cs_test_a1b2c3d4e5f6"
}
```

**Response (erreur - machine déjà avec licence):**
```json
{
  "detail": "Cette machine possède déjà une licence lifetime active"
}
```

### Webhook Stripe

**Endpoint:** `POST /stripe/webhook`

**Configuration Stripe:**
- URL: `https://api.easyfacture.mondher.ch/stripe/webhook`
- Version: Latest API version
- Events: `checkout.session.completed`

**Payload exemple:**
```json
{
  "id": "evt_1XXXXXXX",
  "object": "event",
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_test_...",
      "customer": "cus_...",
      "payment_intent": "pi_...",
      "amount_total": 19900,
      "currency": "eur",
      "metadata": {
        "machine_id": "abc123...",
        "email": "user@example.com",
        "product": "easy_facture_lifetime"
      }
    }
  }
}
```

**Comportement:**
1. Vérifie la signature Stripe (sécurité)
2. Extrait `machine_id` et `email` des metadata
3. Cherche la licence existante (trial)
4. Upgrade `trial` → `lifetime`
5. Génère nouvelle clé de licence lifetime
6. Sauvegarde info Stripe (customer_id, payment_intent, amount)
7. Retourne `{"status": "success"}`

---

## Tests

### Test 1: Créer une session de paiement

```bash
# En mode test Stripe
curl -X POST http://localhost:8000/api/create-checkout-session \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "test_machine_id_12345678901234567890",
    "email": "test@mondher.ch",
    "currency": "eur"
  }'
```

**Attendu:**
- Status 200
- JSON avec `checkout_url` et `session_id`

### Test 2: Simuler paiement Stripe

1. Ouvrir `checkout_url` dans le navigateur
2. Utiliser carte de test: `4242 4242 4242 4242`
3. Date: n'importe quelle date future
4. CVC: n'importe quel 3 chiffres
5. Compléter le paiement

**Attendu:**
- Redirection vers `success_url`
- Webhook appelé automatiquement
- Licence activée en BDD

### Test 3: Vérifier activation

```bash
# Vérifier dans la BDD
docker-compose exec postgres psql -U licenseuser -d easyfacture_licenses -c \
  "SELECT machine_id, license_type, stripe_payment_intent_id, amount_paid
   FROM licenses
   WHERE machine_id = 'test_machine_id_12345678901234567890';"
```

**Attendu:**
- `license_type = 'lifetime'`
- `stripe_payment_intent_id` rempli
- `amount_paid = 19900` (199.00€ en centimes)

### Test 4: Webhook en local (Stripe CLI)

```bash
# Installer Stripe CLI
brew install stripe/stripe-cli/stripe

# Se connecter
stripe login

# Écouter les webhooks et forwarder en local
stripe listen --forward-to localhost:8000/stripe/webhook

# Dans un autre terminal, déclencher un événement test
stripe trigger checkout.session.completed
```

---

## Sécurité

### Points critiques

1. **Vérification signature webhook**
   ```python
   event = stripe.Webhook.construct_event(
       payload, stripe_signature, STRIPE_WEBHOOK_SECRET
   )
   # NE JAMAIS skip cette vérification
   ```

2. **Variables d'environnement**
   - ❌ Ne JAMAIS commiter `.env` dans Git
   - ✅ Utiliser `.env.example` comme template
   - ✅ Stocker secrets dans variables d'environnement serveur

3. **HTTPS obligatoire**
   - Webhook Stripe REFUSE les URLs HTTP
   - Utiliser Let's Encrypt pour SSL gratuit

4. **Rate limiting**
   - 10 requêtes/heure pour `/create-checkout-session`
   - Évite spam et abus

5. **Validation machine_id**
   - Vérifie qu'une machine n'a pas déjà une lifetime
   - Empêche achat multiple

6. **Idempotence webhook**
   - Stripe peut renvoyer le même événement plusieurs fois
   - Utiliser `stripe_payment_intent_id` comme clé unique

---

## Monitoring et logs

### Logs importants à surveiller

```bash
# Voir logs API en temps réel
docker-compose logs -f api

# Rechercher erreurs Stripe
docker-compose logs api | grep "Stripe"

# Vérifier webhooks reçus
docker-compose logs api | grep "stripe/webhook"
```

### Dashboard Stripe

- **Paiements**: https://dashboard.stripe.com/payments
- **Webhooks**: https://dashboard.stripe.com/webhooks
- **Logs**: https://dashboard.stripe.com/logs

**Attention:** En mode test, utiliser https://dashboard.stripe.com/test/...

---

## Troubleshooting

### Erreur: "Configuration Stripe manquante"

**Cause:** Price ID non configuré dans `.env`

**Solution:**
```bash
# Vérifier .env
grep STRIPE_PRICE .env

# Ajouter les price_id depuis Stripe Dashboard
STRIPE_PRICE_EUR=price_1XXXXXXEUR
```

### Erreur: "Invalid signature" sur webhook

**Cause:** `STRIPE_WEBHOOK_SECRET` incorrect

**Solution:**
1. Aller dans Stripe Dashboard > Webhooks
2. Copier le "Signing secret" (whsec_...)
3. Mettre à jour `.env`
4. Redémarrer le serveur

### Webhook non appelé

**Causes possibles:**
1. URL webhook mal configurée dans Stripe
2. Firewall bloque les requêtes Stripe
3. SSL invalide

**Solution:**
```bash
# Vérifier logs Stripe Dashboard
# Vérifier logs serveur
docker-compose logs -f api

# Tester manuellement avec Stripe CLI
stripe trigger checkout.session.completed
```

---

## Prochaines étapes

- [ ] Tester en mode Stripe Test
- [ ] Créer les produits/prix en mode Live
- [ ] Configurer webhook en production
- [ ] Implémenter envoi email de confirmation
- [ ] Ajouter dashboard admin pour voir les paiements
- [ ] Implémenter remboursements (webhook `charge.refunded`)

---

**Documentation créée le:** 2026-01-03
**Dernière mise à jour:** 2026-01-03
**Auteur:** Claude & Mondher
