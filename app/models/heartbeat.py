#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèle Heartbeat - Enregistre les signaux "je suis vivant" des clients
Phase 3 - Heartbeat system
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Heartbeat(Base):
    """Table des heartbeats (signaux périodiques des clients)"""
    __tablename__ = "heartbeats"

    id = Column(Integer, primary_key=True, index=True)

    # Référence à la licence
    license_id = Column(Integer, ForeignKey("licenses.id"), nullable=False, index=True)

    # Informations système
    machine_id = Column(String(64), nullable=False)
    app_version = Column(String(20), nullable=True)
    os_info = Column(String(255), nullable=True)

    # Statistiques d'utilisation (optionnel)
    usage_stats = Column(Text, nullable=True)  # JSON stringifié

    # Timestamp
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relation
    license = relationship("License", back_populates="heartbeats")

    def __repr__(self):
        return f"<Heartbeat(id={self.id}, license_id={self.license_id}, sent_at={self.sent_at})>"
