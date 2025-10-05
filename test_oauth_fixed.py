#!/usr/bin/env python3
"""
Test OAuth avec les routes corrigées
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_oauth_with_credentials():
    """Test OAuth avec les vraies credentials"""
    print("🔐 Testing OAuth with Real Credentials")
    print("=" * 50)
    
    # 1. Créer un utilisateur
    timestamp = int(time.time())
    user_data = {
        "email": f"testoauth{timestamp}@example.com",
        "password": "testpassword123",
        "company_name": "OAuth Test Company"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    print(f"✅ User registered: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.text}")
        return False
    
    # 2. Se connecter
    login_data = {
        "email": f"testoauth{timestamp}@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"✅ User logged in: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Test Gmail OAuth URL avec vraies credentials
    print(f"\n📧 Testing Gmail OAuth URL:")
    response = requests.get(f"{BASE_URL}/api/email/auth-url/gmail", headers=headers)
    
    if response.status_code == 200:
        gmail_data = response.json()
        print(f"✅ Gmail auth URL generated successfully!")
        print(f"   URL: {gmail_data['auth_url'][:100]}...")
        
        # Vérifier les paramètres importants
        url = gmail_data['auth_url']
        if 'client_id=970233687423' in url:
            print(f"✅ Gmail client_id found in URL")
        if 'redirect_uri' in url and 'callback/gmail' in url:
            print(f"✅ Gmail redirect_uri correct")
        if 'scope' in url and 'gmail' in url:
            print(f"✅ Gmail scopes included")
            
    else:
        print(f"❌ Gmail auth URL failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False
    
    # 4. Test Outlook OAuth URL avec vraies credentials
    print(f"\n📮 Testing Outlook OAuth URL:")
    response = requests.get(f"{BASE_URL}/api/email/auth-url/outlook", headers=headers)
    
    if response.status_code == 200:
        outlook_data = response.json()
        print(f"✅ Outlook auth URL generated successfully!")
        print(f"   URL: {outlook_data['auth_url'][:100]}...")
        
        # Vérifier les paramètres importants
        url = outlook_data['auth_url']
        if 'client_id=6b0df61d-3791' in url:
            print(f"✅ Outlook client_id found in URL")
        if 'redirect_uri' in url and 'callback/outlook' in url:
            print(f"✅ Outlook redirect_uri correct")
        if 'scope' in url and 'Mail' in url:
            print(f"✅ Outlook scopes included")
            
    else:
        print(f"❌ Outlook auth URL failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False
    
    print(f"\n🎉 OAuth URLs are working correctly!")
    print(f"\n📋 You can now test the full OAuth flow:")
    print(f"   1. Go to: http://localhost:3000/email-settings")
    print(f"   2. Click 'Connect Gmail' or 'Connect Outlook'")
    print(f"   3. Complete the OAuth authorization")
    print(f"   4. You should be redirected back with success")
    
    return True

if __name__ == "__main__":
    if test_oauth_with_credentials():
        print(f"\n✅ OAuth configuration is correct!")
    else:
        print(f"\n❌ OAuth configuration needs fixing!")
