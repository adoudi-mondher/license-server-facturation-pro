#!/bin/bash
# Easy Facture License Server - Script de vérification du déploiement
# Par Mondher ADOUDI

echo "=========================================="
echo "Easy Facture License Server"
echo "Vérification du déploiement"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction de test
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        return 0
    else
        echo -e "${RED}❌ $1${NC}"
        return 1
    fi
}

# Vérifier que Docker tourne
echo "[1/7] Docker"
docker ps > /dev/null 2>&1
check "Docker est actif"
echo ""

# Vérifier les conteneurs
echo "[2/7] Conteneurs Docker"
docker ps | grep -q "easyfacture-license-api"
check "Conteneur API est en cours d'exécution"

docker ps | grep -q "easyfacture-license-db"
check "Conteneur PostgreSQL est en cours d'exécution"
echo ""

# Vérifier la santé des conteneurs
echo "[3/7] Health checks"
API_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' easyfacture-license-api 2>/dev/null)
if [ "$API_HEALTH" == "healthy" ]; then
    echo -e "${GREEN}✅ API est healthy${NC}"
elif [ "$API_HEALTH" == "starting" ]; then
    echo -e "${YELLOW}⏳ API en cours de démarrage${NC}"
else
    echo -e "${RED}❌ API non healthy (status: $API_HEALTH)${NC}"
fi

DB_HEALTH=$(docker inspect --format='{{.State.Health.Status}}' easyfacture-license-db 2>/dev/null)
if [ "$DB_HEALTH" == "healthy" ]; then
    echo -e "${GREEN}✅ PostgreSQL est healthy${NC}"
else
    echo -e "${RED}❌ PostgreSQL non healthy (status: $DB_HEALTH)${NC}"
fi
echo ""

# Test connexion locale
echo "[4/7] Test connexion locale (port 8000)"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
if [ "$RESPONSE" == "200" ]; then
    echo -e "${GREEN}✅ API répond sur http://localhost:8000${NC}"
else
    echo -e "${RED}❌ API ne répond pas (HTTP $RESPONSE)${NC}"
fi
echo ""

# Test contenu de la réponse
echo "[5/7] Test du health check"
HEALTH_CHECK=$(curl -s http://localhost:8000/health 2>/dev/null)
if echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check retourne 'healthy'${NC}"
    echo "   Réponse: $HEALTH_CHECK"
else
    echo -e "${RED}❌ Health check invalide${NC}"
    echo "   Réponse: $HEALTH_CHECK"
fi
echo ""

# Test de la base de données
echo "[6/7] Test de la base de données"
DB_TEST=$(docker exec easyfacture-license-db psql -U licenseuser -d easyfacture_licenses -c "\dt" 2>/dev/null)
if echo "$DB_TEST" | grep -q "licenses"; then
    echo -e "${GREEN}✅ Table 'licenses' existe${NC}"
else
    echo -e "${YELLOW}⚠️  Table 'licenses' non trouvée (normale au premier démarrage)${NC}"
fi

if echo "$DB_TEST" | grep -q "activations"; then
    echo -e "${GREEN}✅ Table 'activations' existe${NC}"
else
    echo -e "${YELLOW}⚠️  Table 'activations' non trouvée${NC}"
fi
echo ""

# Test API publique (si disponible)
echo "[7/7] Test API publique (optionnel)"
if [ ! -z "$1" ]; then
    PUBLIC_URL="$1"
    echo "   Test sur: $PUBLIC_URL"
    PUBLIC_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$PUBLIC_URL/health" 2>/dev/null)
    if [ "$PUBLIC_RESPONSE" == "200" ]; then
        echo -e "${GREEN}✅ API publique accessible${NC}"
    else
        echo -e "${YELLOW}⚠️  API publique non accessible (HTTP $PUBLIC_RESPONSE)${NC}"
        echo "   Vérifiez Nginx Proxy Manager et le DNS"
    fi
else
    echo -e "${YELLOW}⏭  Test ignoré (fournir l'URL: ./check_deployment.sh https://api.easyfacture.mondher.ch)${NC}"
fi
echo ""

# Résumé
echo "=========================================="
echo "RÉSUMÉ"
echo "=========================================="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep easyfacture
echo ""

# Logs récents
echo "=========================================="
echo "LOGS RÉCENTS (dernières 10 lignes)"
echo "=========================================="
docker compose logs --tail=10 api
echo ""

echo "=========================================="
echo "Pour plus de détails:"
echo "  docker compose logs -f api"
echo "  docker compose logs -f postgres"
echo "=========================================="
