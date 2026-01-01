#!/bin/bash
# Easy Facture License Server - Script de déploiement rapide
# Par Mondher ADOUDI

set -e

echo "=========================================="
echo "Easy Facture License Server"
echo "Script de déploiement Docker"
echo "=========================================="
echo ""

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ ERREUR: Docker n'est pas installé"
    echo "Installez Docker: https://docs.docker.com/engine/install/debian/"
    exit 1
fi

# Vérifier que Docker Compose est installé
if ! docker compose version &> /dev/null; then
    echo "❌ ERREUR: Docker Compose n'est pas installé"
    echo "Installez Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Vérifier si .env existe
if [ ! -f ".env" ]; then
    echo "⚠️  Fichier .env introuvable"
    echo ""
    echo "Création de .env depuis .env.example..."
    cp .env.example .env
    echo "✅ Fichier .env créé"
    echo ""
    echo "⚠️  IMPORTANT: Éditez le fichier .env et remplissez les valeurs:"
    echo "   - POSTGRES_PASSWORD"
    echo "   - SECRET_KEY (générer avec: openssl rand -hex 32)"
    echo "   - ADMIN_PASSWORD"
    echo ""
    read -p "Appuyez sur Entrée après avoir configuré le fichier .env..."
fi

# Vérifier les variables critiques
echo "[1/5] Vérification de la configuration..."
source .env

if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" == "CHANGEME_STRONG_PASSWORD_HERE" ]; then
    echo "❌ ERREUR: POSTGRES_PASSWORD non configuré dans .env"
    exit 1
fi

if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" == "CHANGEME_GENERATE_RANDOM_KEY_HERE" ]; then
    echo "❌ ERREUR: SECRET_KEY non configuré dans .env"
    echo "Générer avec: openssl rand -hex 32"
    exit 1
fi

if [ -z "$LICENSE_SECRET_KEY" ]; then
    echo "❌ ERREUR: LICENSE_SECRET_KEY non configuré dans .env"
    exit 1
fi

echo "   ✅ Configuration valide"
echo ""

# Build des images Docker
echo "[2/5] Build des images Docker..."
docker compose build
echo "   ✅ Images construites"
echo ""

# Arrêter les conteneurs existants (si ils existent)
echo "[3/5] Arrêt des conteneurs existants (si présents)..."
docker compose down 2>/dev/null || true
echo "   ✅ Conteneurs arrêtés"
echo ""

# Démarrer les conteneurs
echo "[4/5] Démarrage des conteneurs..."
docker compose up -d
echo "   ✅ Conteneurs démarrés"
echo ""

# Attendre que l'API soit prête
echo "[5/5] Vérification de l'API..."
echo "   Attente du démarrage (30 secondes)..."
sleep 30

# Test health check
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "   ✅ API opérationnelle"
else
    echo "   ⚠️  L'API ne répond pas encore, vérifiez les logs:"
    echo "      docker compose logs -f api"
fi

echo ""
echo "=========================================="
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "=========================================="
echo ""
echo "🔗 API locale: http://localhost:8000"
echo "🔗 Health check: http://localhost:8000/health"
echo "🔗 Documentation: http://localhost:8000/docs (si ENVIRONMENT=development)"
echo ""
echo "📋 Commandes utiles:"
echo "   docker compose logs -f        # Voir les logs"
echo "   docker compose ps             # État des conteneurs"
echo "   docker compose restart        # Redémarrer"
echo "   docker compose down           # Arrêter"
echo ""
echo "📖 Documentation complète: DEPLOYMENT.md"
echo ""
