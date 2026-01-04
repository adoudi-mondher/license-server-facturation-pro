-- Migration: Ajout des colonnes Stripe au modèle License
-- Date: 2026-01-03
-- Version: 1.0
-- Description: Ajoute les colonnes nécessaires pour gérer les paiements Stripe

-- ==============================================
-- 1. AJOUT DES COLONNES
-- ==============================================

-- Colonnes Stripe Payment Information
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS stripe_session_id VARCHAR(255);
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS stripe_payment_intent_id VARCHAR(255);
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS amount_paid INTEGER;
ALTER TABLE licenses ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'EUR';

-- ==============================================
-- 2. CRÉATION DES INDEX
-- ==============================================

-- Index pour recherche rapide par customer Stripe
CREATE INDEX IF NOT EXISTS idx_licenses_stripe_customer
    ON licenses(stripe_customer_id);

-- Index pour recherche par session Stripe
CREATE INDEX IF NOT EXISTS idx_licenses_stripe_session
    ON licenses(stripe_session_id);

-- Index pour recherche par payment intent
CREATE INDEX IF NOT EXISTS idx_licenses_stripe_payment
    ON licenses(stripe_payment_intent_id);

-- ==============================================
-- 3. VÉRIFICATION
-- ==============================================

-- Afficher la structure de la table
\d licenses

-- Vérifier que les colonnes ont été ajoutées
SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'licenses'
  AND column_name IN (
    'stripe_customer_id',
    'stripe_session_id',
    'stripe_payment_intent_id',
    'amount_paid',
    'currency'
  )
ORDER BY ordinal_position;

-- Vérifier les index créés
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'licenses'
  AND indexname LIKE '%stripe%'
ORDER BY indexname;

-- ==============================================
-- 4. STATISTIQUES (optionnel)
-- ==============================================

-- Compter les licences par type
SELECT license_type, COUNT(*) as count
FROM licenses
GROUP BY license_type
ORDER BY count DESC;

-- Compter les licences avec paiement Stripe
SELECT
    COUNT(*) FILTER (WHERE stripe_payment_intent_id IS NOT NULL) as with_stripe_payment,
    COUNT(*) FILTER (WHERE stripe_payment_intent_id IS NULL) as without_stripe_payment,
    COUNT(*) as total
FROM licenses;

-- ==============================================
-- ROLLBACK (si besoin d'annuler la migration)
-- ==============================================

/*
-- Supprimer les index
DROP INDEX IF EXISTS idx_licenses_stripe_customer;
DROP INDEX IF EXISTS idx_licenses_stripe_session;
DROP INDEX IF EXISTS idx_licenses_stripe_payment;

-- Supprimer les colonnes
ALTER TABLE licenses DROP COLUMN IF EXISTS stripe_customer_id;
ALTER TABLE licenses DROP COLUMN IF EXISTS stripe_session_id;
ALTER TABLE licenses DROP COLUMN IF EXISTS stripe_payment_intent_id;
ALTER TABLE licenses DROP COLUMN IF EXISTS amount_paid;
ALTER TABLE licenses DROP COLUMN IF EXISTS currency;
*/
