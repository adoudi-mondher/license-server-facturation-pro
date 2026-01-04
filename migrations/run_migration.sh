#!/bin/bash
# Script d'exécution de migration pour License Server
# Usage: ./run_migration.sh [migration_file]

set -e  # Arrêter en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}License Server - Migration Database${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Vérifier si on est dans le bon répertoire
if [ ! -f "main.py" ]; then
    echo -e "${RED}Erreur: Lancez ce script depuis le répertoire racine de license-server${NC}"
    exit 1
fi

# Fichier de migration (par défaut: 001_add_stripe_columns.sql)
MIGRATION_FILE=${1:-"migrations/001_add_stripe_columns.sql"}

if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}Erreur: Fichier de migration '$MIGRATION_FILE' introuvable${NC}"
    exit 1
fi

echo -e "${YELLOW}Fichier de migration: $MIGRATION_FILE${NC}"
echo ""

# Détecter l'environnement (Docker ou local)
if command -v docker-compose &> /dev/null && [ -f "docker-compose.yml" ]; then
    echo -e "${GREEN}Environnement détecté: Docker${NC}"
    DOCKER_MODE=true
else
    echo -e "${GREEN}Environnement détecté: Local${NC}"
    DOCKER_MODE=false
fi

echo ""
echo -e "${YELLOW}=== Backup de la base de données ===${NC}"

if [ "$DOCKER_MODE" = true ]; then
    # Backup avec Docker
    BACKUP_FILE="backups/license_db_$(date +%Y%m%d_%H%M%S).sql"
    mkdir -p backups

    echo "Création du backup: $BACKUP_FILE"
    docker-compose exec -T postgres pg_dump -U licenseuser easyfacture_licenses > "$BACKUP_FILE"

    if [ -f "$BACKUP_FILE" ]; then
        echo -e "${GREEN}✓ Backup créé avec succès${NC}"
    else
        echo -e "${RED}✗ Échec de la création du backup${NC}"
        exit 1
    fi
else
    # Backup local
    BACKUP_FILE="backups/license_db_$(date +%Y%m%d_%H%M%S).sql"
    mkdir -p backups

    echo "Création du backup: $BACKUP_FILE"
    pg_dump -U ${POSTGRES_USER:-licenseuser} ${POSTGRES_DB:-easyfacture_licenses} > "$BACKUP_FILE"

    if [ -f "$BACKUP_FILE" ]; then
        echo -e "${GREEN}✓ Backup créé avec succès${NC}"
    else
        echo -e "${RED}✗ Échec de la création du backup${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}=== Exécution de la migration ===${NC}"
echo "Appuyez sur ENTRÉE pour continuer, Ctrl+C pour annuler..."
read

if [ "$DOCKER_MODE" = true ]; then
    # Migration avec Docker
    echo "Exécution de $MIGRATION_FILE dans le conteneur PostgreSQL..."
    docker-compose exec -T postgres psql -U licenseuser -d easyfacture_licenses < "$MIGRATION_FILE"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Migration exécutée avec succès${NC}"
    else
        echo -e "${RED}✗ Échec de la migration${NC}"
        echo ""
        echo -e "${YELLOW}Pour restaurer le backup:${NC}"
        echo "docker-compose exec -T postgres psql -U licenseuser -d easyfacture_licenses < $BACKUP_FILE"
        exit 1
    fi
else
    # Migration locale
    echo "Exécution de $MIGRATION_FILE..."
    psql -U ${POSTGRES_USER:-licenseuser} -d ${POSTGRES_DB:-easyfacture_licenses} < "$MIGRATION_FILE"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Migration exécutée avec succès${NC}"
    else
        echo -e "${RED}✗ Échec de la migration${NC}"
        echo ""
        echo -e "${YELLOW}Pour restaurer le backup:${NC}"
        echo "psql -U ${POSTGRES_USER:-licenseuser} -d ${POSTGRES_DB:-easyfacture_licenses} < $BACKUP_FILE"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}=== Vérification post-migration ===${NC}"

if [ "$DOCKER_MODE" = true ]; then
    echo "Vérification des colonnes Stripe..."
    docker-compose exec -T postgres psql -U licenseuser -d easyfacture_licenses -c \
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='licenses' AND column_name LIKE '%stripe%' ORDER BY column_name;"
else
    echo "Vérification des colonnes Stripe..."
    psql -U ${POSTGRES_USER:-licenseuser} -d ${POSTGRES_DB:-easyfacture_licenses} -c \
        "SELECT column_name, data_type FROM information_schema.columns WHERE table_name='licenses' AND column_name LIKE '%stripe%' ORDER BY column_name;"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Migration terminée avec succès !${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Prochaines étapes:${NC}"
echo "1. Installer la dépendance Stripe:"
if [ "$DOCKER_MODE" = true ]; then
    echo "   docker-compose exec api pip install stripe==8.0.0"
else
    echo "   pip install stripe==8.0.0"
fi
echo ""
echo "2. Configurer les variables Stripe dans .env"
echo ""
echo "3. Redémarrer l'API:"
if [ "$DOCKER_MODE" = true ]; then
    echo "   docker-compose restart api"
else
    echo "   systemctl restart license-server (ou redémarrer manuellement)"
fi
echo ""
echo -e "${YELLOW}Backup sauvegardé dans: $BACKUP_FILE${NC}"
