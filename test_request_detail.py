#!/usr/bin/env python3
"""
Test de la vue détaillée des demandes
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_request_detail():
    """Test de la récupération d'une demande avec détails client"""
    # 1. Créer un utilisateur
    timestamp = int(time.time())
    user_data = {
        "email": f"testdetail{timestamp}@example.com",
        "password": "testpassword123",
        "company_name": "Test Detail Company"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"✅ User registered: {response.status_code}")
    
    # 2. Se connecter
    login_data = {
        "email": f"testdetail{timestamp}@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ User logged in")
    
    # 3. Créer un client
    client_data = {
        "name": "Detail Test Client",
        "email": "detailclient@example.com",
        "company": "Detail Client Company"
    }
    
    response = requests.post(f"{BASE_URL}/clients", json=client_data, headers=headers)
    client_id = response.json()["id"]
    print(f"✅ Client created: {client_id}")
    
    # 4. Créer une demande
    request_data = {
        "title": "Test Detail Request",
        "description": "This is a test request for detail view",
        "client_id": client_id,
        "type": "incoming",
        "priority": "high",
        "email_recipients": ["detailclient@example.com", "test@example.com"]
    }
    
    response = requests.post(f"{BASE_URL}/requests", json=request_data, headers=headers)
    request_id = response.json()["id"]
    print(f"✅ Request created: {request_id}")
    
    # 5. Récupérer la demande avec détails
    response = requests.get(f"{BASE_URL}/requests/{request_id}", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch request detail: {response.status_code} - {response.text}")
        return False
    
    request_detail = response.json()
    print(f"✅ Request detail retrieved:")
    print(f"  - ID: {request_detail['id']}")
    print(f"  - Title: {request_detail['title']}")
    print(f"  - Client Name: {request_detail.get('client_name', 'N/A')}")
    print(f"  - Client Company: {request_detail.get('client_company', 'N/A')}")
    print(f"  - Email Recipients: {request_detail['email_recipients']}")
    print(f"  - Type: {request_detail['type']}")
    print(f"  - Status: {request_detail['status']}")
    
    # Vérifier que les champs client sont présents
    if 'client_name' not in request_detail or 'client_company' not in request_detail:
        print(f"❌ Missing client information in response")
        return False
    
    return True

if __name__ == "__main__":
    print("🔍 Testing Request Detail View")
    print("=" * 40)
    
    if test_request_detail():
        print("\n🎉 Request detail test passed!")
        print("\n🌐 You can now click on requests to view details!")
    else:
        print("\n❌ Request detail test failed!")
