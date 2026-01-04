# Guide de Déploiement - Intégration Stripe

Guide rapide pour déployer l'intégration Stripe en production sur le VPS OVH.

**Temps estimé**: 15-20 minutes

---

## 🚀 Déploiement en Production

### Étape 1: Connexion au VPS

```bash
ssh root@51.38.185.148
cd /root/license-server
```

### Étape 2: Récupérer les modifications

```bash
# Sauvegarder les modifications locales si nécessaire
git stash

# Récupérer les dernières modifications
git pull origin main

# Vérifier les nouveaux fichiers
ls -la app/api/payment.py
ls -la migrations/
```

### Étape 3: Exécuter la migration BDD

```bash
# Rendre le script exécutable (si pas déjà fait)
chmod +x migrations/run_migration.sh

# Exécuter la migration (crée automatiquement un backup)
./migrations/run_migration.sh

# Ou manuellement:
# docker-compose exec -T postgres psql -U licenseuser -d easyfacture_licenses < migrations/001_add_stripe_columns.sql
```

**Résultat attendu:**
```
✓ Backup créé avec succès
✓ Migration exécutée avec succès
```

### Étape 4: Installer Stripe

```bash
# Installer stripe dans le conteneur API
docker-compose exec api pip install stripe==8.0.0

# Vérifier l'installation
docker-compose exec api pip list | grep stripe
# Doit afficher: stripe  8.0.0
```

### Étape 5: Configurer les variables Stripe

```bash
# Éditer le fichier .env
nano .env
```

**Ajouter les variables suivantes** (remplacer XXXXXX par les vraies valeurs):

```bash
# ==============================================
# STRIPE PAYMENT (Licences Lifetime)
# ==============================================
# Clés API Stripe (depuis dashboard.stripe.com)
STRIPE_SECRET_KEY=sk_live_XXXXXX
STRIPE_PUBLISHABLE_KEY=pk_live_XXXXXX

# Webhook secret (depuis Stripe Dashboard > Webhooks)
STRIPE_WEBHOOK_SECRET=whsec_XXXXXX

# Price IDs (depuis Stripe Dashboard > Products)
STRIPE_PRICE_EUR=price_1XXXXXXEUR
STRIPE_PRICE_USD=price_1XXXXXXUSD
STRIPE_PRICE_CHF=price_1XXXXXXCHF
STRIPE_PRICE_GBP=price_1XXXXXXGBP

# URLs de redirection
STRIPE_SUCCESS_URL=https://easyfacture.mondher.ch/payment/success?session_id={CHECKOUT_SESSION_ID}
STRIPE_CANCEL_URL=https://easyfacture.mondher.ch/payment/cancel
```

**Sauvegarder**: `Ctrl+O`, puis `Entrée`, puis `Ctrl+X`

### Étape 6: Redémarrer l'API

```bash
# Redémarrer le conteneur API pour charger les nouvelles variables
docker-compose restart api

# Vérifier que l'API redémarre correctement
docker-compose logs -f api

# Attendre le message: "Application startup complete"
# Ctrl+C pour quitter les logs
```

### Étape 7: Vérifier le déploiement

```bash
# Tester l'endpoint racine
curl https://api.easyfacture.mondher.ch/

# Doit retourner:
# {"name":"EasyFacture License Server","version":"1.0.0","status":"online","environment":"production"}

# Vérifier la documentation API (si activée en dev)
curl https://api.easyfacture.mondher.ch/docs
```

---

## 🧪 Tests de Validation

### Test 1: Vérifier la BDD

```bash
# Se connecter à PostgreSQL
docker-compose exec postgres psql -U licenseuser -d easyfacture_licenses

# Vérifier les colonnes Stripe
\d licenses

# Doit afficher:
# stripe_customer_id      | character varying(255)
# stripe_session_id       | character varying(255)
# stripe_payment_intent_id| character varying(255)
# amount_paid             | integer
# currency                | character varying(3)   | default 'EUR'::character varying

# Quitter PostgreSQL
\q
```

### Test 2: Tester l'endpoint checkout (mode test)

**⚠️ Important**: Utiliser les clés **test** Stripe pour ce test

```bash
# Créer une session de test
curl -X POST https://api.easyfacture.mondher.ch/api/create-checkout-session \
  -H "Content-Type: application/json" \
  -d '{
    "machine_id": "test_machine_12345678901234567890123456",
    "email": "test@mondher.ch",
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

**Si erreur "Configuration Stripe manquante":**
- Vérifier que `STRIPE_PRICE_EUR` est configuré dans `.env`
- Vérifier que la valeur n'est pas `price_XXXXXX_EUR` (placeholder)

### Test 3: Logs de l'API

```bash
# Voir les logs en temps réel
docker-compose logs -f api

# Rechercher des erreurs Stripe
docker-compose logs api | grep -i stripe

# Rechercher des erreurs générales
docker-compose logs api | grep -i error
```

---

## 📋 Configuration Stripe Dashboard

### 1. Créer le produit

1. Aller sur https://dashboard.stripe.com/products
2. Cliquer "Add product"
3. **Name**: Easy Facture - Licence Lifetime
4. **Description**: Licence à vie pour Easy Facture
5. **Pricing**: One-time payment
6. Cliquer "Add product"

### 2. Créer les prix

Pour chaque devise, ajouter un prix:

**EUR (199€):**
- Price: 199.00 EUR
- Type: One-time
- Copier le `price_id` (commence par `price_1...`)

**USD (219$):**
- Price: 219.00 USD
- Type: One-time
- Copier le `price_id`

**CHF (199 CHF):**
- Price: 199.00 CHF
- Type: One-time
- Copier le `price_id`

**GBP (179£):**
- Price: 179.00 GBP
- Type: One-time
- Copier le `price_id`

### 3. Configurer le webhook

1. Aller sur https://dashboard.stripe.com/webhooks
2. Cliquer "Add endpoint"
3. **Endpoint URL**: `https://api.easyfacture.mondher.ch/stripe/webhook`
4. **Events to send**: Sélectionner `checkout.session.completed`
5. **API version**: Latest
6. Cliquer "Add endpoint"
7. **Copier le Signing secret** (`whsec_...`)

---

## 🔒 Sécurité

### Checklist de sécurité

- [ ] Utiliser les clés `sk_live_` et `pk_live_` (pas `sk_test_`)
- [ ] Vérifier que `.env` n'est PAS committé dans Git
- [ ] Webhook secret configuré (`whsec_...`)
- [ ] HTTPS activé (Let's Encrypt)
- [ ] Firewall configuré (ports 80, 443, 22 seulement)
- [ ] Rate limiting activé (10 req/h pour checkout)

### Vérifier la sécurité

```bash
# Vérifier que .env n'est pas tracké par Git
git status | grep .env
# Doit afficher rien ou "Untracked"

# Vérifier les permissions du fichier .env
ls -la .env
# Doit afficher: -rw------- (600)

# Si permissions incorrectes:
chmod 600 .env
```

---

## 🔄 Rollback (en cas de problème)

### Annuler la migration BDD

```bash
# Lister les backups disponibles
ls -lh backups/

# Restaurer le dernier backup
BACKUP_FILE=$(ls -t backups/*.sql | head -1)
echo "Restauration de: $BACKUP_FILE"

docker-compose exec -T postgres psql -U licenseuser -d easyfacture_licenses < "$BACKUP_FILE"
```

### Revenir au code précédent

```bash
# Voir les derniers commits
git log --oneline -5

# Revenir au commit précédent
git checkout <commit_hash>

# Redémarrer l'API
docker-compose restart api
```

---

## 📊 Monitoring

### Vérifier les paiements réussis

```bash
# Voir les licences lifetime créées
docker-compose exec postgres psql -U licenseuser -d easyfacture_licenses -c \
  "SELECT email, license_type, amount_paid, currency, stripe_payment_intent_id, created_at
   FROM licenses
   WHERE license_type = 'lifetime'
   ORDER BY created_at DESC
   LIMIT 10;"
```

### Logs Stripe Dashboard

- **Paiements**: https://dashboard.stripe.com/payments
- **Webhooks**: https://dashboard.stripe.com/webhooks
- **Logs**: https://dashboard.stripe.com/logs

---

## ❓ Troubleshooting

### Problème: "stripe: command not found"

**Solution:**
```bash
docker-compose exec api pip install stripe==8.0.0
docker-compose restart api
```

### Problème: "Configuration Stripe manquante"

**Solution:**
```bash
# Vérifier que les price_id sont configurés
docker-compose exec api env | grep STRIPE_PRICE

# Si vide, éditer .env et redémarrer
docker-compose restart api
```

### Problème: Webhook ne reçoit pas les événements

**Causes possibles:**
1. URL webhook mal configurée dans Stripe
2. SSL invalide
3. Firewall bloque Stripe

**Vérification:**
```bash
# Tester l'accessibilité externe
curl -I https://api.easyfacture.mondher.ch/stripe/webhook

# Voir les logs webhook
docker-compose logs api | grep webhook
```

### Problème: "Invalid signature" sur webhook

**Solution:**
```bash
# Vérifier le webhook secret
docker-compose exec api env | grep STRIPE_WEBHOOK_SECRET

# Doit commencer par whsec_
# Si incorrect, récupérer le bon secret depuis Stripe Dashboard
```

---

## 📝 Checklist finale

- [ ] Migration BDD exécutée avec succès
- [ ] Backup BDD créé
- [ ] Stripe installé (version 8.0.0)
- [ ] Variables Stripe configurées dans `.env`
- [ ] API redémarrée
- [ ] Produit créé dans Stripe Dashboard
- [ ] Prix créés pour EUR, USD, CHF, GBP
- [ ] Webhook configuré dans Stripe Dashboard
- [ ] Test endpoint `/api/create-checkout-session` réussi
- [ ] Logs API sans erreur
- [ ] Sécurité vérifiée (HTTPS, permissions, etc.)

---

**Date de création**: 2026-01-03
**Dernière mise à jour**: 2026-01-03
**Auteur**: Claude & Mondher
