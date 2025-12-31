#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration de la base de données PostgreSQL
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Créer le moteur de base de données
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Vérifie la connexion avant de l'utiliser
    echo=settings.ENVIRONMENT == "development"  # Log SQL en développement
)

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base pour les modèles
Base = declarative_base()


# Dépendance pour obtenir une session de base de données
def get_db():
    """
    Générateur de session de base de données
    Usage dans FastAPI: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
