#!/usr/bin/env python3
"""
Test du statut du frontend
"""

import requests
import time

def test_frontend_status():
    """Test si le frontend répond"""
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        print(f"✅ Frontend status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        return False

def test_backend_status():
    """Test si le backend répond"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        print(f"✅ Backend status: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Backend error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking services status...")
    print("=" * 40)
    
    backend_ok = test_backend_status()
    time.sleep(2)
    frontend_ok = test_frontend_status()
    
    if backend_ok and frontend_ok:
        print("\n🎉 All services are running!")
        print("\n🌐 You can now test the application:")
        print("   - Frontend: http://localhost:3000")
        print("   - Backend API: http://localhost:8000/docs")
        print("\n📝 Try creating a new account and adding requests!")
    else:
        print("\n❌ Some services are not responding correctly.")
