#!/usr/bin/env python3
"""
Test pour vérifier quel client ID Google est actuellement utilisé
"""

import requests
import urllib.parse
import json

def test_current_google_client_id():
    """Vérifie le client ID Google actuel du backend"""
    
    print("🔍 Vérification du Client ID Google utilisé par le backend")
    print("=" * 70)
    
    try:
        # Appeler l'endpoint OAuth Google
        response = requests.get("http://localhost:8000/auth/oauth/google", timeout=5)
        
        if response.status_code != 200:
            print(f"❌ Erreur: Status {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
        
        data = response.json()
        auth_url = data.get('auth_url', '')
        
        # Parser l'URL pour extraire le client_id
        parsed = urllib.parse.urlparse(auth_url)
        params = urllib.parse.parse_qs(parsed.query)
        
        if 'client_id' not in params:
            print("❌ Pas de client_id trouvé dans l'URL OAuth")
            return False
        
        current_client_id = params['client_id'][0]
        
        print(f"\n📋 Client ID actuellement utilisé:")
        print(f"   {current_client_id}")
        
        # Vérifier si c'est le nouveau
        expected_new = "475859287473-99npj0e9pf04qc5v5nt4hqbuvp86cgct.apps.googleusercontent.com"
        old_client_id = "970233687423-j85jdsuupledvaq7qg07fm0ov53pmdgt.apps.googleusercontent.com"
        
        print(f"\n🎯 Attendu (nouveau):")
        print(f"   {expected_new}")
        
        if current_client_id == expected_new:
            print(f"\n✅ CORRECT ! Le backend utilise le NOUVEAU client ID !")
            return True
        elif current_client_id == old_client_id:
            print(f"\n❌ ERREUR ! Le backend utilise encore l'ANCIEN client ID !")
            print(f"\n💡 Solution:")
            print(f"   1. Vérifier que le .env contient le nouveau client ID")
            print(f"   2. Redémarrer Docker: docker-compose down && docker-compose up -d")
            return False
        else:
            print(f"\n⚠️  Client ID inattendu (ni nouveau ni ancien)")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter au backend")
        print(f"   Le backend est-il démarré ? (docker-compose up -d)")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = test_current_google_client_id()
    print("\n" + "=" * 70)
    if success:
        print("✅ Test réussi ! Vous pouvez tester la connexion Google OAuth.")
    else:
        print("❌ Test échoué ! Corrigez le problème avant de continuer.")

