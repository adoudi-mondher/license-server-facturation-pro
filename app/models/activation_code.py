#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèle ActivationCode - Codes d'activation pré-générés (Phase 4)
Pour vente via revendeurs ou activation offline
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from app.database import Base


class ActivationCode(Base):
    """Table des codes d'activation pré-générés"""
    __tablename__ = "activation_codes"

    id = Column(Integer, primary_key=True, index=True)

    # Code unique
    code = Column(String(64), unique=True, nullable=False, index=True)

    # Type de licence associée
    license_type = Column(String(50), nullable=False)

    # Statut
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    used_by_email = Column(String(255), nullable=True)
    used_by_machine_id = Column(String(64), nullable=True)

    # Dates
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # NULL = pas d'expiration

    # Métadonnées
    batch_id = Column(String(50), nullable=True, index=True)  # Pour grouper les codes
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ActivationCode(id={self.id}, code={self.code}, used={self.is_used})>"
