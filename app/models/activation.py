#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèle Activation - Enregistre chaque vérification de licence
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Activation(Base):
    """Table des activations (vérifications de licence)"""
    __tablename__ = "activations"

    id = Column(Integer, primary_key=True, index=True)

    # Référence à la licence
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False, index=True)

    # Informations de vérification
    machine_id = Column(String(64), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(255), nullable=True)

    # Résultat de la vérification
    is_valid = Column(Boolean, nullable=False)
    validation_message = Column(Text, nullable=True)

    # Timestamp
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relation
    license = relationship("License", back_populates="activations")

    def __repr__(self):
        return f"<Activation(id={self.id}, license_id={self.license_id}, valid={self.is_valid})>"
