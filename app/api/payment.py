#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Endpoints pour les paiements Stripe
Gestion des achats de licences lifetime - Version Production Sécurisée
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import stripe
import os

from app.database import get_db
from app.schemas.license import (
    CreateCheckoutSessionRequest,
    CheckoutSessionResponse
)
from app.models.license import License
from app.utils.license_crypto import license_generator
from app.config import settings
from app.utils.mailer import send_license_email

# Router
router = APIRouter(prefix="/api", tags=["Payment"])

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Configuration Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Prix Stripe par devise
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
    Crée une session Stripe Checkout avec gestion fine des erreurs

    Supporte 2 flux:
    1. Depuis l'app (machine_id + email connus)
    2. Depuis landing page (machine_id et email inconnus -> PENDING)
    """

    # 1. Gestion propre de l'exception "Déjà licencié" (Évite l'erreur 400 brute)
    if checkout_request.machine_id and "PENDING" not in checkout_request.machine_id:
        existing_lifetime = db.query(License).filter(
            License.machine_id == checkout_request.machine_id,
            License.license_type == "lifetime",
            License.is_active == True
        ).first()

        if existing_lifetime:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "ALREADY_ACTIVE",
                    "message": "Une licence est déjà active sur cet ordinateur."
                }
            )

    # 2. Vérification de la configuration
    currency = checkout_request.currency.lower()
    price_id = STRIPE_PRICES.get(currency)

    if not price_id or price_id.startswith('price_XXXXXX'):
        raise HTTPException(
            status_code=500,
            detail={"code": "CONFIG_ERROR", "message": f"Configuration Stripe manquante pour {currency.upper()}"}
        )

    try:
        # 3. Logique d'email intelligent pour la Landing Page
        customer_email = None
        if checkout_request.email and "@" in checkout_request.email:
            # Si c'est un placeholder (test/pending), on laisse Stripe demander l'email
            if all(x not in checkout_request.email.lower() for x in ["test", "pending"]):
                customer_email = checkout_request.email

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',
            allow_promotion_codes=True,
            success_url=os.environ.get('STRIPE_SUCCESS_URL'),
            cancel_url=os.environ.get('STRIPE_CANCEL_URL'),
            customer_email=customer_email,
            metadata={
                'machine_id': checkout_request.machine_id if checkout_request.machine_id else "PENDING",
                'email': checkout_request.email if checkout_request.email else "PENDING",
                'product': 'easy_facture_lifetime'
            }
        )

        return CheckoutSessionResponse(
            success=True,
            checkout_url=session.url,
            session_id=session.id
        )

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=503, detail={"code": "STRIPE_ERROR", "message": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "INTERNAL_ERROR", "message": "Erreur interne serveur"})


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """
    Webhook Stripe pour activer les licences après paiement réussi

    Gère 2 scénarios:
    1. Achat depuis l'app: machine_id connu -> activation immédiate
    2. Achat depuis landing page: machine_id PENDING -> envoi email avec clé
       (le client activera manuellement plus tard)
    """
    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        # Sécurité Webhook renforcée
        raise HTTPException(status_code=403, detail="Signature invalide")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Extraction robuste de l'email
        email = session['metadata'].get('email')
        if not email or "pending" in email.lower() or "test" in email.lower():
            # Fallback: email collecté par Stripe au checkout
            email = session.get('customer_details', {}).get('email')

        if not email:
            # Cas impossible normalement (Stripe force l'email)
            return {"status": "error", "message": "No email found"}

        # Extraction du machine_id
        machine_id = session['metadata'].get('machine_id')
        if not machine_id or machine_id == "PENDING":
            # Achat depuis landing page -> génération machine_id temporaire
            machine_id = f"PENDING_LINK_{session.get('id')[:10]}"

        # Extraction info Stripe pour sauvegarde
        stripe_customer_id = session.get('customer')
        stripe_session_id = session.get('id')
        stripe_payment_intent_id = session.get('payment_intent')
        amount_paid = session.get('amount_total')
        currency = session.get('currency', 'EUR').upper()

        # Vérifier si une licence existe déjà pour cet email ou machine
        existing_license = db.query(License).filter(
            (License.machine_id == machine_id) | (License.email == email)
        ).first()

        if existing_license:
            # Mise à jour d'une licence existante (trial -> lifetime)
            existing_license.license_type = "lifetime"
            existing_license.email = email
            existing_license.expires_at = None  # Lifetime = pas d'expiration
            existing_license.is_active = True
            existing_license.is_revoked = False

            # Si on avait un machine_id temporaire et qu'on en reçoit un vrai
            if "PENDING_LINK" in existing_license.machine_id and "PENDING_LINK" not in machine_id:
                existing_license.machine_id = machine_id

            # Infos Stripe
            existing_license.stripe_customer_id = stripe_customer_id
            existing_license.stripe_session_id = stripe_session_id
            existing_license.stripe_payment_intent_id = stripe_payment_intent_id
            existing_license.amount_paid = amount_paid
            existing_license.currency = currency

            # Regénération de la clé lifetime
            license_key, _ = license_generator.generate_license(
                machine_id=existing_license.machine_id,
                email=email,
                license_type="lifetime",
                duration_days=None
            )
            existing_license.license_key = license_key

            db.commit()

        else:
            # Création d'une nouvelle licence lifetime
            license_key, _ = license_generator.generate_license(
                machine_id=machine_id,
                email=email,
                license_type="lifetime",
                duration_days=None
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
                stripe_customer_id=stripe_customer_id,
                stripe_session_id=stripe_session_id,
                stripe_payment_intent_id=stripe_payment_intent_id,
                amount_paid=amount_paid,
                currency=currency
            )
            db.add(new_license)
            db.commit()

        # --- ENVOI DE L'EMAIL AVEC LA CLÉ ---
        # Que ce soit depuis l'app ou la landing page, on envoie toujours l'email
        background_tasks.add_task(send_license_email, email, license_key)

        return {"status": "success", "message": "License created/updated and email queued"}

    return {"status": "ignored"}


@router.get("/get-license-by-session/{session_id}")
async def get_license_by_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Récupère la clé de licence par session_id Stripe
    Utilisé par la page success après paiement
    """
    # Chercher la licence par stripe_session_id
    license_record = db.query(License).filter(
        License.stripe_session_id == session_id
    ).first()

    if not license_record:
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": "Licence non trouvée pour cette session"}
        )

    return {
        "success": True,
        "license_key": license_record.license_key,
        "email": license_record.email,
        "license_type": license_record.license_type
    }
