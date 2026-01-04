#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endpoints pour les paiements Stripe
Gestion des achats de licences lifetime
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime
import stripe
import os

from app.database import get_db
from app.schemas.license import (
    CreateCheckoutSessionRequest,
    CheckoutSessionResponse,
    ErrorResponse
)
from app.models.license import License
from app.utils.license_crypto import license_generator
from app.config import settings

# Router
router = APIRouter(prefix="/api", tags=["Payment"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Configuration Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Prix Stripe par devise (à configurer dans le .env ou settings)
STRIPE_PRICES = {
    'eur': os.environ.get('STRIPE_PRICE_EUR', 'price_XXXXXX_EUR'),
    'usd': os.environ.get('STRIPE_PRICE_USD', 'price_XXXXXX_USD'),
    'chf': os.environ.get('STRIPE_PRICE_CHF', 'price_XXXXXX_CHF'),
    'gbp': os.environ.get('STRIPE_PRICE_GBP', 'price_XXXXXX_GBP'),
}


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
@limiter.limit("10/hour")
async def create_checkout_session(
    request: Request,
    checkout_request: CreateCheckoutSessionRequest,
    db: Session = Depends(get_db)
):
    """
    Crée une session Stripe Checkout pour acheter une licence lifetime

    **Rate limit**: 10 requêtes par heure par IP

    **Logique**:
    1. Vérifie si la machine n'a pas déjà une licence lifetime
    2. Crée une session Stripe Checkout
    3. Retourne l'URL de paiement
    """

    # Vérifier si la machine a déjà une licence lifetime
    existing_lifetime = db.query(License).filter(
        License.machine_id == checkout_request.machine_id,
        License.license_type == "lifetime",
        License.is_active == True
    ).first()

    if existing_lifetime:
        raise HTTPException(
            status_code=400,
            detail="Cette machine possède déjà une licence lifetime active"
        )

    # Récupérer le price_id selon la devise
    currency = checkout_request.currency.lower()
    price_id = STRIPE_PRICES.get(currency)

    if not price_id or price_id.startswith('price_XXXXXX'):
        raise HTTPException(
            status_code=500,
            detail=f"Configuration Stripe manquante pour la devise {currency.upper()}"
        )

    try:
        # Créer la session Stripe Checkout
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=os.environ.get(
                'STRIPE_SUCCESS_URL',
                'https://easyfacture.mondher.ch/payment/success?session_id={CHECKOUT_SESSION_ID}'
            ),
            cancel_url=os.environ.get(
                'STRIPE_CANCEL_URL',
                'https://easyfacture.mondher.ch/payment/cancel'
            ),
            customer_email=checkout_request.email,
            metadata={
                'machine_id': checkout_request.machine_id,
                'email': checkout_request.email,
                'product': 'easy_facture_lifetime'
            }
        )

        return CheckoutSessionResponse(
            success=True,
            checkout_url=session.url,
            session_id=session.id
        )

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur Stripe: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la création de la session: {str(e)}"
        )


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """
    Webhook Stripe pour traiter les paiements réussis

    **Événements traités**:
    - checkout.session.completed: Active la licence lifetime après paiement

    **Sécurité**:
    - Vérifie la signature Stripe obligatoirement
    """

    payload = await request.body()

    # Vérifier la signature Stripe (CRITIQUE pour la sécurité)
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Payload invalide
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        # Signature invalide
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Traiter l'événement checkout.session.completed
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Extraire les métadonnées
        machine_id = session['metadata'].get('machine_id')
        email = session['metadata'].get('email')

        if not machine_id or not email:
            raise HTTPException(
                status_code=400,
                detail="Missing metadata in session"
            )

        # Vérifier si une licence existe déjà pour cette machine
        existing_license = db.query(License).filter(
            License.machine_id == machine_id
        ).first()

        if existing_license:
            # Mettre à jour la licence existante (trial → lifetime)
            existing_license.license_type = "lifetime"
            existing_license.email = email
            existing_license.expires_at = None  # Lifetime = pas d'expiration
            existing_license.is_active = True
            existing_license.is_revoked = False
            existing_license.stripe_customer_id = session.get('customer')
            existing_license.stripe_session_id = session.get('id')
            existing_license.stripe_payment_intent_id = session.get('payment_intent')
            existing_license.amount_paid = session.get('amount_total')
            existing_license.currency = session.get('currency', 'EUR').upper()

            # Regénérer une clé de licence lifetime
            license_key, _ = license_generator.generate_license(
                machine_id=machine_id,
                email=email,
                license_type="lifetime",
                duration_days=None,  # Lifetime
                customer_name=existing_license.customer_name,
                company_name=existing_license.company_name
            )

            existing_license.license_key = license_key

        else:
            # Créer une nouvelle licence lifetime (cas rare)
            license_key, _ = license_generator.generate_license(
                machine_id=machine_id,
                email=email,
                license_type="lifetime",
                duration_days=None,  # Lifetime
                customer_name=None,
                company_name=None
            )

            new_license = License(
                email=email,
                customer_name=None,
                company_name=None,
                machine_id=machine_id,
                license_type="lifetime",
                license_key=license_key,
                expires_at=None,  # Lifetime
                is_active=True,
                is_revoked=False,
                stripe_customer_id=session.get('customer'),
                stripe_session_id=session.get('id'),
                stripe_payment_intent_id=session.get('payment_intent'),
                amount_paid=session.get('amount_total'),
                currency=session.get('currency', 'EUR').upper()
            )

            db.add(new_license)

        db.commit()

        # TODO: Envoyer email de confirmation
        # send_license_confirmation_email(email, machine_id, license_key)

        return {"status": "success", "message": "License activated"}

    # Autres événements ignorés
    return {"status": "ignored"}
