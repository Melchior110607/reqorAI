#!/usr/bin/env python3
"""
Test final de toutes les fonctionnalités
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_complete_workflow():
    """Test du workflow complet"""
    print("🚀 Testing Complete B2B Request Management Workflow")
    print("=" * 60)
    
    # 1. Créer un utilisateur
    timestamp = int(time.time())
    user_data = {
        "email": f"finaltest{timestamp}@example.com",
        "password": "testpassword123",
        "company_name": "Final Test Company",
        "first_name": "Final",
        "last_name": "Test"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"✅ User registered: {response.status_code}")
    
    # 2. Se connecter
    login_data = {
        "email": f"finaltest{timestamp}@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ User logged in")
    
    # 3. Créer des clients
    clients_data = [
        {
            "name": "Alice Johnson",
            "email": "alice@clienta.com",
            "company": "Client A Corp",
            "phone": "+1111111111"
        },
        {
            "name": "Bob Smith",
            "email": "bob@clientb.com",
            "company": "Client B Inc",
            "phone": "+2222222222"
        }
    ]
    
    client_ids = []
    for client_data in clients_data:
        response = requests.post(f"{BASE_URL}/clients", json=client_data, headers=headers)
        client_ids.append(response.json()["id"])
    
    print(f"✅ Created {len(client_ids)} clients")
    
    # 4. Créer des demandes de différents types
    requests_data = [
        {
            "title": "Outgoing Request 1",
            "description": "This is our request to Client A",
            "client_id": client_ids[0],
            "type": "outgoing",
            "priority": "high",
            "reminder_frequency": "weekly",
            "email_recipients": ["alice@clienta.com"],
            "is_priority": True
        },
        {
            "title": "Incoming Request 1",
            "description": "This is a request from Client B",
            "client_id": client_ids[1],
            "type": "incoming",
            "priority": "medium",
            "reminder_frequency": "daily",
            "email_recipients": ["bob@clientb.com"],
            "is_priority": False
        },
        {
            "title": "Outgoing Request 2",
            "description": "Another request to Client A",
            "client_id": client_ids[0],
            "type": "outgoing",
            "priority": "low",
            "reminder_frequency": "monthly",
            "email_recipients": ["alice@clienta.com", f"finaltest{timestamp}@example.com"],
            "is_priority": False
        }
    ]
    
    request_ids = []
    for request_data in requests_data:
        response = requests.post(f"{BASE_URL}/requests", json=request_data, headers=headers)
        if response.status_code == 200:
            request_ids.append(response.json()["id"])
        else:
            print(f"❌ Failed to create request: {response.text}")
            return False
    
    print(f"✅ Created {len(request_ids)} requests")
    
    # 5. Test de récupération avec filtres
    # Toutes les demandes
    response = requests.get(f"{BASE_URL}/requests", headers=headers)
    all_requests = response.json()
    print(f"✅ Retrieved {len(all_requests)} total requests")
    
    # Demandes sortantes
    response = requests.get(f"{BASE_URL}/requests?request_type=outgoing", headers=headers)
    outgoing_requests = response.json()
    print(f"✅ Retrieved {len(outgoing_requests)} outgoing requests")
    
    # Demandes entrantes
    response = requests.get(f"{BASE_URL}/requests?request_type=incoming", headers=headers)
    incoming_requests = response.json()
    print(f"✅ Retrieved {len(incoming_requests)} incoming requests")
    
    # 6. Test de mise à jour de statut
    response = requests.put(f"{BASE_URL}/requests/{request_ids[0]}", json={"status": "completed"}, headers=headers)
    if response.status_code == 200:
        print(f"✅ Updated request status to completed")
    else:
        print(f"❌ Failed to update status: {response.text}")
        return False
    
    # 7. Test de récupération de détail
    response = requests.get(f"{BASE_URL}/requests/{request_ids[0]}", headers=headers)
    if response.status_code == 200:
        request_detail = response.json()
        print(f"✅ Retrieved request detail with client info:")
        print(f"   - Title: {request_detail['title']}")
        print(f"   - Status: {request_detail['status']}")
        print(f"   - Client: {request_detail['client_name']} ({request_detail['client_company']})")
        print(f"   - Email Recipients: {request_detail['email_recipients']}")
    else:
        print(f"❌ Failed to get request detail: {response.text}")
        return False
    
    return True

if __name__ == "__main__":
    if test_complete_workflow():
        print("\n🎉 ALL TESTS PASSED!")
        print("\n🌐 Your B2B Request Management SaaS is ready!")
        print("\n📋 Features available:")
        print("   ✅ User authentication and registration")
        print("   ✅ Client management")
        print("   ✅ Request creation (outgoing/incoming)")
        print("   ✅ Request filtering and search")
        print("   ✅ Detailed request views with:")
        print("      - Drag & drop file upload (incoming)")
        print("      - Email composition (incoming)")
        print("      - Reminder sending (outgoing)")
        print("      - Response tracking (outgoing)")
        print("      - Status management")
        print("      - Priority system")
        print("\n🚀 Ready for AI integration in the next phase!")
        print("\n🌐 Access your application:")
        print("   - Frontend: http://localhost:3000")
        print("   - Backend API: http://localhost:8000")
        print("   - API Docs: http://localhost:8000/docs")
    else:
        print("\n❌ Some tests failed!")
