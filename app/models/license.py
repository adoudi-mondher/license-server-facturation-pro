#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modèle License - Représente une licence générée
"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class License(Base):
    """Table des licences"""
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)

    # Informations client
    email = Column(String(255), index=True, nullable=False)
    customer_name = Column(String(255))
    company_name = Column(String(255))

    # Identifiant machine
    machine_id = Column(String(64), index=True, nullable=False)

    # Type de licence
    license_type = Column(String(50), nullable=False)  # trial, monthly, annual, lifetime, etc.

    # Clé de licence (chiffrée)
    license_key = Column(Text, nullable=False, unique=True)

    # Dates
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=True, index=True)  # NULL pour lifetime

    # Statut
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(Text, nullable=True)

    # Métadonnées
    notes = Column(Text, nullable=True)  # Notes admin

    # 🆕 Stripe Payment Information (pour licences lifetime achetées)
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    stripe_session_id = Column(String(255), nullable=True, index=True)
    stripe_payment_intent_id = Column(String(255), nullable=True, index=True)
    amount_paid = Column(Integer, nullable=True)  # Montant en centimes (19900 = 199.00€)
    currency = Column(String(3), default='EUR', nullable=True)

    # Relations
    activations = relationship("Activation", back_populates="license", cascade="all, delete-orphan")
    heartbeats = relationship("Heartbeat", back_populates="license", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<License(id={self.id}, email={self.email}, type={self.license_type})>"
