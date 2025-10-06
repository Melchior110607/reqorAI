import json
import requests
from urllib.parse import quote
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from msal import ConfidentialClientApplication
from app.models.email_connection import EmailConnection, EmailProvider, ConnectionStatus
from app.database.config import settings

class OutlookService:
    def __init__(self, db: Session):
        self.db = db
        self.scopes = ['User.Read', 'Mail.Read', 'Mail.Send', 'offline_access']
        self.authority = 'https://login.microsoftonline.com/common'
        
        if not settings.outlook_client_id or not settings.outlook_client_secret:
            raise Exception("Outlook OAuth credentials not configured")
        
        self.app = ConfidentialClientApplication(
            client_id=settings.outlook_client_id,
            client_credential=settings.outlook_client_secret,
            authority=self.authority
        )

    def get_auth_url(self, user_id: int) -> str:
        """Génère l'URL d'authentification Outlook"""
        # Déterminer l'URL de callback selon le type d'authentification
        if user_id == -1:
            # Authentification principale
            redirect_uri = f"{settings.base_url}/auth/oauth/callback/microsoft"
        else:
            # Ajout de canal email
            redirect_uri = f"{settings.base_url}/email/callback/outlook"
        
        # Construire l'URL manuellement pour plus de contrôle
        auth_url = (
            f"{self.authority}/oauth2/v2.0/authorize?"
            f"client_id={settings.outlook_client_id}&"
            f"response_type=code&"
            f"redirect_uri={quote(redirect_uri)}&"
            f"response_mode=query&"
            f"scope={quote(' '.join(self.scopes))}&"
            f"state={user_id}"
        )
        
        return auth_url

    def handle_oauth_callback(self, code: str, state: str) -> EmailConnection:
        """Gère le callback OAuth et crée la connexion"""
        user_id = int(state)
        
        # Échanger le code contre des tokens
        result = self.app.acquire_token_by_authorization_code(
            code=code,
            scopes=self.scopes,
            redirect_uri=f"{settings.base_url}/api/email/callback/outlook"
        )
        
        if 'error' in result:
            raise Exception(f"OAuth error: {result.get('error_description', result['error'])}")
        
        access_token = result['access_token']
        refresh_token = result.get('refresh_token')
        
        # Obtenir l'adresse email de l'utilisateur
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
        
        if response.status_code != 200:
            raise Exception("Failed to get user profile from Microsoft Graph")
        
        profile = response.json()
        email_address = profile['mail'] or profile['userPrincipalName']
        
        # Créer ou mettre à jour la connexion
        connection = self.db.query(EmailConnection).filter(
            EmailConnection.user_id == user_id,
            EmailConnection.provider == EmailProvider.OUTLOOK,
            EmailConnection.email_address == email_address
        ).first()
        
        if not connection:
            connection = EmailConnection(
                user_id=user_id,
                provider=EmailProvider.OUTLOOK,
                email_address=email_address
            )
            self.db.add(connection)
        
        connection.access_token = access_token
        connection.refresh_token = refresh_token
        connection.expires_at = result.get('expires_in')  # TODO: Calculer la vraie date d'expiration
        connection.status = ConnectionStatus.ACTIVE
        
        self.db.commit()
        self.db.refresh(connection)
        
        return connection

    def refresh_token(self, connection: EmailConnection) -> bool:
        """Rafraîchit le token d'accès"""
        try:
            if not connection.refresh_token:
                return False
            
            result = self.app.acquire_token_by_refresh_token(
                refresh_token=connection.refresh_token,
                scopes=self.scopes
            )
            
            if 'error' in result:
                connection.status = ConnectionStatus.ERROR
                self.db.commit()
                return False
            
            connection.access_token = result['access_token']
            connection.status = ConnectionStatus.ACTIVE
            
            self.db.commit()
            return True
            
        except Exception as e:
            connection.status = ConnectionStatus.ERROR
            self.db.commit()
            return False

    def get_recent_emails(self, connection: EmailConnection, max_results: int = 10) -> List[Dict[str, Any]]:
        """Récupère les emails récents"""
        try:
            headers = {'Authorization': f'Bearer {connection.access_token}'}
            
            # Récupérer les messages récents
            url = f'https://graph.microsoft.com/v1.0/me/messages?$top={max_results}&$orderby=receivedDateTime desc'
            response = requests.get(url, headers=headers)
            
            if response.status_code == 401:
                # Token expiré, essayer de le rafraîchir
                if self.refresh_token(connection):
                    headers['Authorization'] = f'Bearer {connection.access_token}'
                    response = requests.get(url, headers=headers)
                else:
                    return []
            
            if response.status_code != 200:
                print(f"Error fetching Outlook emails: {response.status_code} - {response.text}")
                return []
            
            messages = response.json().get('value', [])
            emails = []
            
            for message in messages:
                email_data = self._parse_outlook_message(message)
                emails.append(email_data)
            
            return emails
            
        except Exception as e:
            print(f"Error fetching Outlook emails: {e}")
            return []

    def _parse_outlook_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse un message Outlook"""
        sender = message.get('sender', {}).get('emailAddress', {})
        
        return {
            'id': message['id'],
            'thread_id': message.get('conversationId', ''),
            'sender_email': sender.get('address', ''),
            'sender_name': sender.get('name', ''),
            'subject': message.get('subject', ''),
            'body': message.get('body', {}).get('content', ''),
            'received_at': message.get('receivedDateTime', ''),
            'attachments': []  # TODO: Implémenter extraction des pièces jointes
        }

    def setup_webhook(self, connection: EmailConnection) -> bool:
        """Configure un webhook pour recevoir les emails en temps réel"""
        try:
            headers = {
                'Authorization': f'Bearer {connection.access_token}',
                'Content-Type': 'application/json'
            }
            
            subscription_data = {
                'changeType': 'created',
                'notificationUrl': f"{settings.base_url}/api/email/webhook/outlook",
                'resource': 'me/messages',
                'expirationDateTime': '2024-01-01T00:00:00.0000000Z',  # TODO: Calculer date d'expiration
                'clientState': str(connection.id)
            }
            
            response = requests.post(
                'https://graph.microsoft.com/v1.0/subscriptions',
                headers=headers,
                json=subscription_data
            )
            
            if response.status_code == 201:
                subscription = response.json()
                connection.webhook_url = subscription['id']
                self.db.commit()
                return True
            else:
                print(f"Failed to create webhook: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error setting up webhook: {e}")
            return False
