#!/usr/bin/env python3
"""
Test spécifique pour les email_recipients
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_email_recipients():
    """Test des email_recipients avec différents cas"""
    # 1. Créer un utilisateur
    timestamp = int(time.time())
    user_data = {
        "email": f"testemail{timestamp}@example.com",
        "password": "testpassword123",
        "company_name": "Test Email Company"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"✅ User registered: {response.status_code}")
    
    # 2. Se connecter
    login_data = {
        "email": f"testemail{timestamp}@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ User logged in")
    
    # 3. Créer un client
    client_data = {
        "name": "Email Test Client",
        "email": "emailtest@example.com",
        "company": "Email Test Company"
    }
    
    response = requests.post(f"{BASE_URL}/clients", json=client_data, headers=headers)
    client_id = response.json()["id"]
    print(f"✅ Client created: {client_id}")
    
    # 4. Test avec email_recipients vide
    request_data_empty = {
        "title": "Request with empty emails",
        "description": "Test empty email recipients",
        "client_id": client_id,
        "type": "outgoing",
        "priority": "medium",
        "email_recipients": []
    }
    
    response = requests.post(f"{BASE_URL}/requests", json=request_data_empty, headers=headers)
    if response.status_code != 200:
        print(f"❌ Empty emails failed: {response.status_code} - {response.text}")
        return False
    
    request_id_empty = response.json()["id"]
    print(f"✅ Request with empty emails created: {request_id_empty}")
    
    # 5. Test avec email_recipients rempli
    request_data_filled = {
        "title": "Request with filled emails",
        "description": "Test filled email recipients",
        "client_id": client_id,
        "type": "incoming",
        "priority": "high",
        "email_recipients": ["test1@example.com", "test2@example.com"]
    }
    
    response = requests.post(f"{BASE_URL}/requests", json=request_data_filled, headers=headers)
    if response.status_code != 200:
        print(f"❌ Filled emails failed: {response.status_code} - {response.text}")
        return False
    
    request_id_filled = response.json()["id"]
    print(f"✅ Request with filled emails created: {request_id_filled}")
    
    # 6. Récupérer toutes les demandes
    response = requests.get(f"{BASE_URL}/requests", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch requests: {response.status_code} - {response.text}")
        return False
    
    all_requests = response.json()
    print(f"✅ Retrieved {len(all_requests)} requests")
    
    # Vérifier les email_recipients
    for req in all_requests:
        print(f"  - Request {req['id']}: email_recipients = {req['email_recipients']} (type: {type(req['email_recipients'])})")
        if not isinstance(req['email_recipients'], list):
            print(f"❌ email_recipients is not a list for request {req['id']}")
            return False
    
    # 7. Test de mise à jour
    update_data = {
        "email_recipients": ["updated@example.com"]
    }
    
    response = requests.put(f"{BASE_URL}/requests/{request_id_empty}", json=update_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Update failed: {response.status_code} - {response.text}")
        return False
    
    updated_request = response.json()
    print(f"✅ Request updated: email_recipients = {updated_request['email_recipients']}")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing email_recipients handling")
    print("=" * 50)
    
    if test_email_recipients():
        print("\n🎉 All email_recipients tests passed!")
    else:
        print("\n❌ Some email_recipients tests failed!")
