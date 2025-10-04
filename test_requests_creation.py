#!/usr/bin/env python3
"""
Test spécifique pour la création de demandes
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_request_creation_flow():
    """Test complet du flow de création de demandes"""
    print("🧪 Testing complete request creation flow")
    
    # 1. Créer un utilisateur
    timestamp = int(time.time())
    user_data = {
        "email": f"testreq{timestamp}@example.com",
        "password": "testpassword123",
        "company_name": "Test Request Company",
        "first_name": "Request",
        "last_name": "Test"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"✅ User registered: {response.status_code}")
    
    # 2. Se connecter
    login_data = {
        "email": f"testreq{timestamp}@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ User logged in")
    
    # 3. Créer un client
    client_data = {
        "name": "Test Request Client",
        "email": "requestclient@example.com",
        "company": "Request Client Company",
        "phone": "+1234567890",
        "address": "123 Test Street"
    }
    
    response = requests.post(f"{BASE_URL}/clients", json=client_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Client creation failed: {response.text}")
        return False
    
    client_id = response.json()["id"]
    print(f"✅ Client created: {client_id}")
    
    # 4. Créer une demande sortante
    outgoing_request = {
        "title": "Test Outgoing Request",
        "description": "This is a test outgoing request",
        "client_id": client_id,
        "type": "outgoing",
        "priority": "high",
        "reminder_frequency": "weekly",
        "email_recipients": ["requestclient@example.com"],
        "is_priority": True
    }
    
    response = requests.post(f"{BASE_URL}/requests", json=outgoing_request, headers=headers)
    if response.status_code != 200:
        print(f"❌ Outgoing request creation failed: {response.status_code} - {response.text}")
        return False
    
    outgoing_id = response.json()["id"]
    print(f"✅ Outgoing request created: {outgoing_id}")
    
    # 5. Créer une demande entrante
    incoming_request = {
        "title": "Test Incoming Request",
        "description": "This is a test incoming request",
        "client_id": client_id,
        "type": "incoming",
        "priority": "medium",
        "reminder_frequency": "daily",
        "email_recipients": ["requestclient@example.com"],
        "is_priority": False
    }
    
    response = requests.post(f"{BASE_URL}/requests", json=incoming_request, headers=headers)
    if response.status_code != 200:
        print(f"❌ Incoming request creation failed: {response.status_code} - {response.text}")
        return False
    
    incoming_id = response.json()["id"]
    print(f"✅ Incoming request created: {incoming_id}")
    
    # 6. Récupérer toutes les demandes
    response = requests.get(f"{BASE_URL}/requests", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch requests: {response.status_code} - {response.text}")
        return False
    
    all_requests = response.json()
    print(f"✅ Retrieved {len(all_requests)} requests")
    
    # 7. Récupérer les demandes sortantes
    response = requests.get(f"{BASE_URL}/requests?request_type=outgoing", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch outgoing requests: {response.status_code} - {response.text}")
        return False
    
    outgoing_requests = response.json()
    print(f"✅ Retrieved {len(outgoing_requests)} outgoing requests")
    
    # 8. Récupérer les demandes entrantes
    response = requests.get(f"{BASE_URL}/requests?request_type=incoming", headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch incoming requests: {response.status_code} - {response.text}")
        return False
    
    incoming_requests = response.json()
    print(f"✅ Retrieved {len(incoming_requests)} incoming requests")
    
    # 9. Mettre à jour une demande
    update_data = {
        "title": "Updated Request Title",
        "status": "completed"
    }
    
    response = requests.put(f"{BASE_URL}/requests/{outgoing_id}", json=update_data, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to update request: {response.status_code} - {response.text}")
        return False
    
    print(f"✅ Request updated successfully")
    
    return True

if __name__ == "__main__":
    print("🚀 Testing Request Creation and Management")
    print("=" * 60)
    
    if test_request_creation_flow():
        print("\n🎉 All request tests passed!")
        print("\n🌐 Frontend should now work correctly at: http://localhost:3000")
    else:
        print("\n❌ Some tests failed!")
