#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitaires de cryptographie pour les licences
Doit être IDENTIQUE au système utilisé dans EasyFacture client
"""

import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from app.config import settings


class LicenseGenerator:
    """
    Générateur de clés de licence chiffrées
    Compatible avec le système LicenseManager de EasyFacture
    """

    def __init__(self):
        """Initialise le générateur avec la clé secrète"""
        self.cipher = Fernet(settings.LICENSE_SECRET_KEY.encode())

    def generate_license(
        self,
        machine_id: str,
        email: str,
        license_type: str,
        duration_days: int = None,
        customer_name: str = None,
        company_name: str = None
    ) -> tuple[str, datetime]:
        """
        Génère une clé de licence chiffrée

        Args:
            machine_id: Identifiant unique de la machine
            email: Email du client
            license_type: Type de licence (trial, monthly, annual, lifetime, etc.)
            duration_days: Durée en jours (None pour lifetime)
            customer_name: Nom du client (optionnel)
            company_name: Nom de l'entreprise (optionnel)

        Returns:
            tuple: (license_key, expires_at)
                - license_key: Clé de licence chiffrée (str)
                - expires_at: Date d'expiration (datetime) ou None pour lifetime
        """
        # Calculer la date d'expiration
        expires_at = None
        if duration_days is not None:
            expires_at = datetime.utcnow() + timedelta(days=duration_days)

        # Créer le payload de la licence
        # IMPORTANT: Utiliser 'expiry' et non 'expires_at' pour compatibilité avec EasyFacture client (license.py ligne 104)
        license_data = {
            "machine_id": machine_id,
            "email": email,
            "expiry": expires_at.isoformat() if expires_at else None,  # 'expiry' pour compatibilité!
            "version": "1.7.0",
            "generated": datetime.utcnow().isoformat()
        }

        # Convertir en JSON et chiffrer
        json_data = json.dumps(license_data, ensure_ascii=False)
        encrypted = self.cipher.encrypt(json_data.encode('utf-8'))

        # IMPORTANT: Retourner en HEX pour compatibilité avec EasyFacture (license.py ligne 113)
        license_key = encrypted.hex()

        return license_key, expires_at

    def validate_license(self, license_key: str, machine_id: str) -> tuple[bool, str, dict]:
        """
        Valide une clé de licence

        Args:
            license_key: Clé de licence chiffrée
            machine_id: Identifiant de la machine courante

        Returns:
            tuple: (is_valid, message, license_data)
                - is_valid: True si licence valide
                - message: Message descriptif
                - license_data: Données déchiffrées (dict) ou None
        """
        try:
            # Déchiffrer la licence depuis HEX (compatibilité license.py ligne 138)
            encrypted_bytes = bytes.fromhex(license_key)
            decrypted = self.cipher.decrypt(encrypted_bytes)
            license_data = json.loads(decrypted.decode('utf-8'))

            # Vérifier le Machine ID
            if license_data.get("machine_id") != machine_id:
                return False, "Licence invalide pour cette machine", None

            # Vérifier l'expiration (utiliser 'expiry' pour compatibilité avec EasyFacture)
            expiry_str = license_data.get("expiry")
            if expiry_str:
                expiry = datetime.fromisoformat(expiry_str)
                if datetime.utcnow() > expiry:
                    return False, "Licence expirée", None

            # Licence valide
            license_type = license_data.get("license_type", "unknown")
            return True, f"Licence valide ({license_type})", license_data

        except Exception as e:
            return False, f"Licence invalide ou corrompue: {str(e)}", None


# Instance globale
license_generator = LicenseGenerator()
