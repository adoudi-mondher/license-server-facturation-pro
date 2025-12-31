#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration de l'API License Server
Charge les variables d'environnement depuis .env
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configuration de l'application"""

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    LICENSE_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "EasyFacture License Server"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Convertit la chaîne CORS_ORIGINS en liste"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Rate Limiting
    TRIAL_RATE_LIMIT: str = "3/hour"
    VALIDATE_RATE_LIMIT: str = "100/hour"

    # Trial Configuration
    DEFAULT_TRIAL_DAYS: int = 30

    # Email (optionnel)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    # Admin
    ADMIN_EMAIL: str = "admin@mondher.ch"
    ADMIN_PASSWORD: str = "changeme"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Instance globale de configuration
settings = Settings()
