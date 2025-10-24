import json
import requests
import socket
from urllib.parse import quote
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from msal import ConfidentialClientApplication
from requests.exceptions import RequestException, ConnectionError, Timeout
from app.models.email_connection import EmailConnection, EmailProvider, ConnectionStatus
from app.database.config import settings


class NetworkError(Exception):
    """Erreur réseau temporaire - ne pas marquer la connexion en ERROR"""
    pass


class AuthenticationError(Exception):
    """Erreur d'authentification - peut nécessiter reconnexion"""
    pass

class OutlookService:
    def __init__(self, db: Session):
        self.db = db
        # Note: Ne PAS inclure 'offline_access', 'openid', 'profile' 
        # MSAL les ajoute automatiquement et cela cause une erreur frozenset
        # Utiliser les scopes Graph API complets pour éviter les conflits
        self.scopes = ['https://graph.microsoft.com/User.Read', 
                       'https://graph.microsoft.com/Mail.Read', 
                       'https://graph.microsoft.com/Mail.Send']
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
        
        # Déterminer l'URL de callback utilisée (doit matcher get_auth_url)
        callback_url = f"{settings.base_url}/email/callback/outlook"
        
        # Échanger le code contre des tokens
        # Note: MSAL ajoute automatiquement openid, profile, offline_access
        # On doit passer les scopes comme une liste explicite
        result = self.app.acquire_token_by_authorization_code(
            code=code,
            scopes=list(self.scopes),  # Convertir explicitement en list
            redirect_uri=callback_url
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
        
        # Calculer la date d'expiration réelle (expires_in est en secondes)
        from datetime import datetime, timedelta, timezone
        expires_in_seconds = result.get('expires_in', 3600)  # Défaut 1h
        connection.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        
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

    def get_recent_emails(self, connection: EmailConnection, max_results: int = 10, since_timestamp: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Récupère les emails récents, optionnellement depuis une date donnée"""
        try:
            # ✅ VÉRIFICATION RÉSEAU PRÉALABLE (Outlook uniquement)
            # Check si l'appareil est connecté avant de tenter l'appel API
            try:
                socket.setdefaulttimeout(2)
                socket.gethostbyname('login.microsoftonline.com')
                print(f"🌐 Network check OK for Outlook ({connection.email_address})")
            except (socket.gaierror, socket.timeout) as e:
                error_msg = f"No network connectivity detected: {type(e).__name__}"
                print(f"🌐 {error_msg}")
                raise NetworkError(error_msg)
            
            headers = {'Authorization': f'Bearer {connection.access_token}'}
            
            # Construire l'URL avec filtre de date si fourni
            url = f'https://graph.microsoft.com/v1.0/me/messages?$top={max_results}&$orderby=receivedDateTime desc'
            if since_timestamp:
                # Outlook utilise le format ISO 8601: 2025-10-06T10:00:00Z
                date_str = since_timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')
                url += f'&$filter=receivedDateTime ge {date_str}'
            
            # Timeout de 10 secondes pour éviter de bloquer trop longtemps
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 401:
                # Token expiré, essayer de le rafraîchir
                print(f"🔄 Outlook token expired for {connection.email_address}, refreshing...")
                if self.refresh_token(connection):
                    headers['Authorization'] = f'Bearer {connection.access_token}'
                    response = requests.get(url, headers=headers, timeout=10)
                else:
                    raise AuthenticationError("Failed to refresh token")
            
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                print(f"⚠️ Error fetching Outlook emails: {error_msg}")
                raise AuthenticationError(error_msg)
            
            messages = response.json().get('value', [])
            emails = []
            
            for message in messages:
                email_data = self._parse_outlook_message(message)
                emails.append(email_data)
            
            print(f"✅ Fetched {len(emails)} Outlook emails for {connection.email_address}")
            return emails
            
        except (ConnectionError, Timeout) as e:
            # Erreurs réseau temporaires - NE PAS marquer en ERROR
            error_msg = f"Network error (temporary): {type(e).__name__} - {str(e)}"
            print(f"🌐 {error_msg}")
            raise NetworkError(error_msg)
            
        except RequestException as e:
            # Autres erreurs réseau
            error_msg = f"Request error: {type(e).__name__} - {str(e)}"
            print(f"🌐 {error_msg}")
            raise NetworkError(error_msg)
            
        except AuthenticationError:
            # Réamorcer l'exception auth
            raise
            
        except Exception as e:
            # Autres erreurs inattendues
            error_msg = f"Unexpected error: {type(e).__name__} - {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def get_emails_from_delta(self, connection: EmailConnection, delta_link: str) -> List[Dict[str, Any]]:
        """
        Récupère uniquement les NOUVEAUX emails depuis un deltaLink donné
        Utilise l'API Delta de Microsoft Graph pour une efficacité maximale
        """
        try:
            headers = {'Authorization': f'Bearer {connection.access_token}'}
            
            # Utiliser le deltaLink pour récupérer SEULEMENT les changements
            response = requests.get(delta_link, headers=headers, timeout=10)
            
            if response.status_code == 401:
                # Token expiré
                if self.refresh_token(connection):
                    headers['Authorization'] = f'Bearer {connection.access_token}'
                    response = requests.get(delta_link, headers=headers, timeout=10)
                else:
                    raise AuthenticationError("Failed to refresh token")
            
            if response.status_code != 200:
                print(f"⚠️ Delta API error: {response.status_code}, falling back to recent emails")
                return self.get_recent_emails(connection, max_results=10)
            
            data = response.json()
            messages = data.get('value', [])
            
            # Filtrer uniquement les nouveaux messages (pas les suppressions/modifications)
            new_messages = [msg for msg in messages if '@removed' not in msg]
            
            emails = []
            for message in new_messages:
                email_data = self._parse_outlook_message(message)
                emails.append(email_data)
            
            print(f"✅ Fetched {len(emails)} NEW emails from delta for {connection.email_address}")
            return emails
            
        except Exception as e:
            print(f"❌ Error fetching delta: {str(e)}, falling back")
            return self.get_recent_emails(connection, max_results=10)

    def _parse_outlook_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse un message Outlook"""
        sender = message.get('sender', {}).get('emailAddress', {})
        
        # Parser la date ISO 8601 de Microsoft en datetime Python
        date_str = message.get('receivedDateTime', '')
        try:
            # Format Outlook: 2025-10-06T11:30:37Z
            received_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception as e:
            print(f"Error parsing Outlook date '{date_str}': {e}")
            received_at = datetime.now()
        
        # Extraire le corps du message (text seulement si disponible, sinon HTML)
        body_content = message.get('body', {})
        body_text = body_content.get('content', '')
        
        # Si le body est en HTML, on pourrait le nettoyer ici si nécessaire
        # Pour l'instant on garde tel quel
        
        return {
            'id': message['id'],
            'thread_id': message.get('conversationId', ''),
            'sender_email': sender.get('address', ''),
            'sender_name': sender.get('name', ''),
            'subject': message.get('subject', ''),
            'body': body_text,
            'received_at': received_at,  # Maintenant c'est un datetime Python
            'attachments': []  # TODO: Implémenter extraction des pièces jointes
        }
    
    def send_email(
        self, 
        connection: EmailConnection, 
        to_email: str, 
        subject: str, 
        body: str,
        attachments: list = None
    ) -> Dict[str, Any]:
        """Send email via Microsoft Graph API with optional attachments"""
        try:
            headers = {
                'Authorization': f'Bearer {connection.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Create message payload
            message_payload = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "Text",
                        "content": body
                    },
                    "toRecipients": [
                        {
                            "emailAddress": {
                                "address": to_email
                            }
                        }
                    ]
                },
                "saveToSentItems": "true"
            }
            
            # Add attachments if provided
            if attachments and len(attachments) > 0:
                import base64
                message_payload["message"]["attachments"] = []
                
                for attachment_info in attachments:
                    file_path = attachment_info['path']
                    filename = attachment_info['filename']
                    
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                        encoded_content = base64.b64encode(file_content).decode('utf-8')
                    
                    message_payload["message"]["attachments"].append({
                        "@odata.type": "#microsoft.graph.fileAttachment",
                        "name": filename,
                        "contentBytes": encoded_content
                    })
                
                print(f"📎 Added {len(attachments)} attachment(s) to email")
            
            # Send message
            response = requests.post(
                'https://graph.microsoft.com/v1.0/me/sendMail',
                headers=headers,
                json=message_payload,
                timeout=30
            )
            
            if response.status_code == 202:
                print(f"📧 Email sent via Outlook to {to_email}")
                return {
                    'success': True,
                    'to': to_email
                }
            else:
                error_msg = f"Failed to send email: HTTP {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)

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
