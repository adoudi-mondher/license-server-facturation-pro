#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endpoints pour la gestion des licences
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime

from app.database import get_db
from app.schemas.license import (
    TrialRequest,
    LicenseResponse,
    ValidateRequest,
    ValidationResponse,
    ErrorResponse
)
from app.models.license import License
from app.models.activation import Activation
from app.utils.license_crypto import license_generator
from app.config import settings

# Router
router = APIRouter(prefix="/licenses", tags=["Licenses"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post("/trial", response_model=LicenseResponse)
@limiter.limit(settings.TRIAL_RATE_LIMIT)
async def request_trial(
    request: Request,
    trial_request: TrialRequest,
    db: Session = Depends(get_db)
):
    """
    Génère une licence d'essai (30 jours)

    **Rate limit**: 3 requêtes par heure par IP

    **Logique**:
    1. Vérifie si une licence trial existe déjà pour cet email ou machine_id
    2. Si oui, refuse (une seule trial par client)
    3. Si non, génère une nouvelle licence trial de 30 jours
    4. Sauvegarde dans la base de données
    5. Retourne la clé de licence chiffrée
    """
    # Vérifier si déjà une trial pour cet email
    existing_email = db.query(License).filter(
        License.email == trial_request.email,
        License.license_type == "trial"
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Une licence d'essai existe déjà pour cet email"
        )

    # Vérifier si déjà une trial pour cette machine
    existing_machine = db.query(License).filter(
        License.machine_id == trial_request.machine_id,
        License.license_type == "trial"
    ).first()

    if existing_machine:
        raise HTTPException(
            status_code=400,
            detail="Une licence d'essai existe déjà pour cette machine"
        )

    # Générer la licence trial (30 jours)
    license_key, expires_at = license_generator.generate_license(
        machine_id=trial_request.machine_id,
        email=trial_request.email,
        license_type="trial",
        duration_days=settings.DEFAULT_TRIAL_DAYS,
        customer_name=trial_request.customer_name,
        company_name=trial_request.company_name
    )

    # Créer l'entrée en base de données
    new_license = License(
        email=trial_request.email,
        customer_name=trial_request.customer_name,
        company_name=trial_request.company_name,
        machine_id=trial_request.machine_id,
        license_type="trial",
        license_key=license_key,
        expires_at=expires_at,
        is_active=True,
        is_revoked=False
    )

    db.add(new_license)
    db.commit()
    db.refresh(new_license)

    # Retourner la réponse
    return LicenseResponse(
        success=True,
        message="Licence d'essai générée avec succès",
        license_key=license_key,
        expires_at=expires_at,
        license_type="trial"
    )


@router.post("/validate", response_model=ValidationResponse)
@limiter.limit(settings.VALIDATE_RATE_LIMIT)
async def validate_license(
    request: Request,
    validate_request: ValidateRequest,
    db: Session = Depends(get_db)
):
    """
    Valide une clé de licence

    **Rate limit**: 100 requêtes par heure par IP

    **Logique**:
    1. Déchiffre et valide la clé de licence
    2. Vérifie le machine_id
    3. Vérifie l'expiration
    4. Vérifie le statut (active, non révoquée)
    5. Enregistre l'activation dans la table activations
    6. Retourne le résultat de validation
    """
    # Valider cryptographiquement la licence
    is_valid_crypto, message, license_data = license_generator.validate_license(
        validate_request.license_key,
        validate_request.machine_id
    )

    if not is_valid_crypto:
        # Enregistrer l'échec
        activation = Activation(
            license_id=None,  # Licence non trouvée
            machine_id=validate_request.machine_id,
            ip_address=request.client.host if request.client else None,
            is_valid=False,
            validation_message=message
        )
        db.add(activation)
        db.commit()

        return ValidationResponse(
            valid=False,
            message=message
        )

    # Rechercher la licence en base de données
    license_record = db.query(License).filter(
        License.license_key == validate_request.license_key
    ).first()

    if not license_record:
        # Licence valide cryptographiquement mais pas en base
        activation = Activation(
            license_id=None,
            machine_id=validate_request.machine_id,
            ip_address=request.client.host if request.client else None,
            is_valid=False,
            validation_message="Licence introuvable dans la base de données"
        )
        db.add(activation)
        db.commit()

        return ValidationResponse(
            valid=False,
            message="Licence introuvable"
        )

    # Vérifier si révoquée
    if license_record.is_revoked:
        activation = Activation(
            license_id=license_record.id,
            machine_id=validate_request.machine_id,
            ip_address=request.client.host if request.client else None,
            is_valid=False,
            validation_message=f"Licence révoquée: {license_record.revoked_reason or 'Raison non spécifiée'}"
        )
        db.add(activation)
        db.commit()

        return ValidationResponse(
            valid=False,
            message=f"Licence révoquée: {license_record.revoked_reason or 'Contactez le support'}"
        )

    # Vérifier si active
    if not license_record.is_active:
        activation = Activation(
            license_id=license_record.id,
            machine_id=validate_request.machine_id,
            ip_address=request.client.host if request.client else None,
            is_valid=False,
            validation_message="Licence inactive"
        )
        db.add(activation)
        db.commit()

        return ValidationResponse(
            valid=False,
            message="Licence inactive"
        )

    # Calculer les jours restants
    days_remaining = None
    if license_record.expires_at:
        delta = license_record.expires_at - datetime.utcnow()
        days_remaining = max(0, delta.days)

    # Licence valide - enregistrer l'activation
    activation = Activation(
        license_id=license_record.id,
        machine_id=validate_request.machine_id,
        ip_address=request.client.host if request.client else None,
        is_valid=True,
        validation_message="Licence valide"
    )
    db.add(activation)
    db.commit()

    return ValidationResponse(
        valid=True,
        message="Licence valide",
        expires_at=license_record.expires_at,
        days_remaining=days_remaining,
        license_type=license_record.license_type
    )
