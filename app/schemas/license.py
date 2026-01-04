#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schémas Pydantic pour les licences
Validation des requêtes/réponses API
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


# ============================================
# REQUEST SCHEMAS
# ============================================

class TrialRequest(BaseModel):
    """Requête pour obtenir une licence d'essai"""
    email: EmailStr
    machine_id: str = Field(..., min_length=32, max_length=64)
    customer_name: Optional[str] = None
    company_name: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "customer_name": "Jean Dupont",
                "company_name": "Dupont SARL"
            }
        }


class ActivateRequest(BaseModel):
    """Requête pour activer une licence"""
    activation_code: str = Field(..., min_length=10)
    machine_id: str = Field(..., min_length=32, max_length=64)
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "activation_code": "EASY-FACT-2024-XXXXX",
                "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "email": "user@example.com"
            }
        }


class ValidateRequest(BaseModel):
    """Requête pour valider une licence"""
    license_key: str = Field(..., min_length=100)
    machine_id: str = Field(..., min_length=32, max_length=64)

    class Config:
        json_schema_extra = {
            "example": {
                "license_key": "gAAAAABk...",  # Clé chiffrée
                "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
            }
        }


class HeartbeatRequest(BaseModel):
    """Requête heartbeat (Phase 3)"""
    license_key: str
    machine_id: str
    app_version: Optional[str] = None
    os_info: Optional[str] = None
    usage_stats: Optional[dict] = None


class CreateCheckoutSessionRequest(BaseModel):
    """Requête pour créer une session Stripe Checkout"""
    machine_id: str = Field(..., min_length=32, max_length=64)
    email: EmailStr
    currency: Optional[str] = Field(default='eur', pattern='^(eur|usd|chf|gbp)$')

    class Config:
        json_schema_extra = {
            "example": {
                "machine_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "email": "user@example.com",
                "currency": "eur"
            }
        }


class StripeWebhookEvent(BaseModel):
    """Événement reçu du webhook Stripe (simplifié)"""
    type: str
    data: dict

    class Config:
        json_schema_extra = {
            "example": {
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test_...",
                        "metadata": {
                            "machine_id": "abc123...",
                            "email": "user@example.com"
                        }
                    }
                }
            }
        }


# ============================================
# RESPONSE SCHEMAS
# ============================================

class LicenseResponse(BaseModel):
    """Réponse contenant une licence"""
    success: bool
    message: str
    license_key: str
    expires_at: Optional[datetime]
    license_type: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Licence d'essai générée avec succès",
                "license_key": "gAAAAABk...",
                "expires_at": "2024-02-15T10:30:00",
                "license_type": "trial"
            }
        }


class ValidationResponse(BaseModel):
    """Réponse de validation de licence"""
    valid: bool
    message: str
    expires_at: Optional[datetime] = None
    days_remaining: Optional[int] = None
    license_type: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "message": "Licence valide",
                "expires_at": "2024-02-15T10:30:00",
                "days_remaining": 25,
                "license_type": "trial"
            }
        }


class CheckoutSessionResponse(BaseModel):
    """Réponse contenant l'URL de la session Stripe Checkout"""
    success: bool
    checkout_url: str
    session_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
                "session_id": "cs_test_..."
            }
        }


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée"""
    success: bool = False
    error: str
    details: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Invalid license key",
                "details": "The provided license key format is invalid"
            }
        }
