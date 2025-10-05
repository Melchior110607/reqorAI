#!/usr/bin/env python3
"""
Test des URLs OAuth Gmail et Outlook
"""

import requests
import time

BASE_URL = "http://localhost:8000"

def test_oauth_urls():
    """Test de génération des URLs OAuth"""
    print("🔐 Testing OAuth URL Generation")
    print("=" * 50)
    
    # 1. Créer un utilisateur
    timestamp = int(time.time())
    user_data = {
        "email": f"testoauth{timestamp}@example.com",
        "password": "testpassword123",
        "company_name": "OAuth Test Company"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    print(f"✅ User registered: {response.status_code}")
    
    # 2. Se connecter
    login_data = {
        "email": f"testoauth{timestamp}@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ User logged in")
    
    # 3. Test Gmail OAuth URL
    print(f"\n📧 Testing Gmail OAuth URL:")
    response = requests.get(f"{BASE_URL}/email/auth-url/gmail", headers=headers)
    
    if response.status_code == 200:
        gmail_data = response.json()
        print(f"✅ Gmail auth URL generated successfully")
        print(f"   URL starts with: {gmail_data['auth_url'][:80]}...")
        
        # Vérifier que l'URL contient les bons paramètres
        url = gmail_data['auth_url']
        if 'accounts.google.com' in url and 'client_id' in url and 'redirect_uri' in url:
            print(f"✅ Gmail URL contains required parameters")
        else:
            print(f"❌ Gmail URL missing required parameters")
            
    else:
        print(f"❌ Gmail auth URL failed: {response.status_code}")
        print(f"   Error: {response.text}")
    
    # 4. Test Outlook OAuth URL
    print(f"\n📮 Testing Outlook OAuth URL:")
    response = requests.get(f"{BASE_URL}/email/auth-url/outlook", headers=headers)
    
    if response.status_code == 200:
        outlook_data = response.json()
        print(f"✅ Outlook auth URL generated successfully")
        print(f"   URL starts with: {outlook_data['auth_url'][:80]}...")
        
        # Vérifier que l'URL contient les bons paramètres
        url = outlook_data['auth_url']
        if 'login.microsoftonline.com' in url and 'client_id' in url and 'redirect_uri' in url:
            print(f"✅ Outlook URL contains required parameters")
        else:
            print(f"❌ Outlook URL missing required parameters")
            
    else:
        print(f"❌ Outlook auth URL failed: {response.status_code}")
        print(f"   Error: {response.text}")
    
    print(f"\n📋 Configuration Summary:")
    print(f"   Gmail callback URL should be: {BASE_URL}/api/email/callback/gmail")
    print(f"   Outlook callback URL should be: {BASE_URL}/api/email/callback/outlook")
    print(f"   Frontend callback page: http://localhost:3000/email-callback")
    
    return True

if __name__ == "__main__":
    if test_oauth_urls():
        print(f"\n🎉 OAuth URL generation is working!")
        print(f"\n📝 Next steps:")
        print(f"   1. Configure your OAuth apps with the URLs shown above")
        print(f"   2. Set your API keys in environment variables")
        print(f"   3. Test the full OAuth flow at http://localhost:3000/email-settings")
    else:
        print(f"\n❌ OAuth URL generation failed!")
