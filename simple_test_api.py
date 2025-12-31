#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API de test simple sans FastAPI (pour démonstration)
Lance un serveur HTTP basique qui répond aux requêtes de licence
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime, timedelta
import sys
import os

# Ajouter le répertoire parent au path pour importer app
sys.path.insert(0, os.path.dirname(__file__))

# Simuler les imports
from cryptography.fernet import Fernet

# Clé de chiffrement (IDENTIQUE à celle dans facturation-app/app/utils/license.py ligne 312)
# NOTE: Il y a 2 classes LicenseManager, Python utilise la 2ème (ligne 304)
LICENSE_SECRET_KEY = b'QvS9Dy6SjhpVPFf-nsu2NZ-xPfS3-Xaom--vwvdeH6w='

# Stockage en mémoire des licences (pour le test)
licenses_db = {}


def generate_license(machine_id, email, license_type="trial", duration_days=30):
    """Génère une licence chiffrée"""
    cipher = Fernet(LICENSE_SECRET_KEY)

    expires_at = datetime.utcnow() + timedelta(days=duration_days)

    # IMPORTANT: Format IDENTIQUE à license.py (lignes 101-107)
    license_data = {
        "email": email,
        "machine_id": machine_id,
        "expiry": expires_at.isoformat(),  # 'expiry' pas 'expires_at' !
        "version": "1.6.0",
        "generated": datetime.utcnow().isoformat()
    }

    json_data = json.dumps(license_data, ensure_ascii=False)
    encrypted = cipher.encrypt(json_data.encode('utf-8'))
    # IMPORTANT: Convertir en HEX pour compatibilité avec license.py (ligne 113)
    license_key = encrypted.hex()

    return license_key, expires_at


class LicenseAPIHandler(BaseHTTPRequestHandler):
    """Handler pour les requêtes API"""

    def do_POST(self):
        """Traite les requêtes POST"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            self.send_error(400, "Invalid JSON")
            return

        # Route: /api/v1/licenses/trial
        if self.path == '/api/v1/licenses/trial':
            self.handle_trial_request(data)

        # Route: /api/v1/licenses/validate
        elif self.path == '/api/v1/licenses/validate':
            self.handle_validate_request(data)

        else:
            self.send_error(404, "Not Found")

    def handle_trial_request(self, data):
        """Génère une licence trial"""
        email = data.get('email')
        machine_id = data.get('machine_id')

        if not email or not machine_id:
            self.send_json_response(400, {
                "detail": "Email et machine_id requis"
            })
            return

        # Vérifier si déjà existe (simple check en mémoire)
        key = f"{email}_{machine_id}"
        if key in licenses_db:
            self.send_json_response(400, {
                "detail": "Une licence d'essai existe déjà pour cet email ou cette machine"
            })
            return

        # Générer la licence
        license_key, expires_at = generate_license(machine_id, email, "trial", 30)

        # Stocker en mémoire
        licenses_db[key] = {
            "license_key": license_key,
            "expires_at": expires_at.isoformat(),
            "is_revoked": False
        }

        # Réponse
        self.send_json_response(200, {
            "success": True,
            "message": "Licence d'essai générée avec succès",
            "license_key": license_key,
            "expires_at": expires_at.isoformat(),
            "license_type": "trial"
        })

        print(f"✅ Trial créé pour {email} (Machine: {machine_id[:8]}...)")

    def handle_validate_request(self, data):
        """Valide une licence"""
        license_key = data.get('license_key')
        machine_id = data.get('machine_id')

        if not license_key or not machine_id:
            self.send_json_response(400, {
                "detail": "license_key et machine_id requis"
            })
            return

        # Pour le test, on accepte toutes les licences valides cryptographiquement
        try:
            cipher = Fernet(LICENSE_SECRET_KEY)
            # Convertir depuis HEX (compatibilité license.py ligne 138)
            encrypted_bytes = bytes.fromhex(license_key)
            decrypted = cipher.decrypt(encrypted_bytes)
            license_data = json.loads(decrypted.decode('utf-8'))

            # Vérifier machine_id
            if license_data.get("machine_id") != machine_id:
                self.send_json_response(200, {
                    "valid": False,
                    "message": "Licence invalide pour cette machine"
                })
                return

            # Vérifier expiration (champ 'expiry' comme dans license.py)
            expiry_str = license_data.get("expiry")
            if expiry_str:
                expiry = datetime.fromisoformat(expiry_str)
                if datetime.utcnow() > expiry:
                    self.send_json_response(200, {
                        "valid": False,
                        "message": "Licence expirée"
                    })
                    return

                days_remaining = (expiry - datetime.utcnow()).days
            else:
                days_remaining = None

            # Licence valide
            self.send_json_response(200, {
                "valid": True,
                "message": "Licence valide",
                "expires_at": expiry_str,
                "days_remaining": days_remaining,
                "license_type": "trial"  # Pour compatibilité avec le client API
            })

            print(f"✅ Validation réussie pour Machine {machine_id[:8]}...")

        except Exception as e:
            self.send_json_response(200, {
                "valid": False,
                "message": f"Licence invalide: {str(e)}"
            })

    def send_json_response(self, status_code, data):
        """Envoie une réponse JSON"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        """Override pour réduire les logs"""
        pass


def run_server(port=8000):
    """Lance le serveur"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, LicenseAPIHandler)

    print("=" * 60)
    print("LICENSE SERVER - TEST MODE")
    print("=" * 60)
    print(f"Serveur démarré sur http://127.0.0.1:{port}")
    print(f"")
    print(f"Endpoints disponibles:")
    print(f"  POST /api/v1/licenses/trial")
    print(f"  POST /api/v1/licenses/validate")
    print(f"")
    print(f"Appuyez sur Ctrl+C pour arrêter")
    print("=" * 60)
    print()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nArrêt du serveur...")
        httpd.shutdown()


if __name__ == '__main__':
    run_server()
