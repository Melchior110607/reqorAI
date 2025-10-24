import base64
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from email.utils import parsedate_to_datetime
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from requests.exceptions import RequestException, ConnectionError, Timeout
from sqlalchemy.orm import Session
from app.models.email_connection import EmailConnection, EmailProvider, ConnectionStatus
from app.database.config import settings
from sqlalchemy.sql import func


class NetworkError(Exception):
    """Erreur réseau temporaire - ne pas marquer la connexion en ERROR"""
    pass


class AuthenticationError(Exception):
    """Erreur d'authentification - peut nécessiter reconnexion"""
    pass

class GmailService:
    def __init__(self, db: Session):
        self.db = db
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify',
            'https://mail.google.com/'
        ]

    def get_auth_url(self, user_id: int) -> str:
        """Génère l'URL d'authentification Gmail"""
        if not settings.gmail_client_id or not settings.gmail_client_secret:
            raise Exception("Gmail OAuth credentials not configured")
        
        # Déterminer l'URL de callback selon le type d'authentification
        if user_id == -1:
            # Authentification principale
            callback_url = f"{settings.base_url}/auth/oauth/callback/google"
        else:
            # Ajout de canal email
            callback_url = f"{settings.base_url}/email/callback/gmail"
            
        client_config = {
            "web": {
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [callback_url]
            }
        }
        
        flow = Flow.from_client_config(client_config, scopes=self.scopes)
        flow.redirect_uri = callback_url
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=str(user_id),
            prompt='consent'  # Force consent screen pour refresh token
        )
        
        return auth_url

    def handle_oauth_callback(self, code: str, state: str) -> EmailConnection:
        """Gère le callback OAuth et crée la connexion"""
        user_id = int(state)
        
        # Déterminer l'URL de callback utilisée (doit matcher get_auth_url)
        callback_url = f"{settings.base_url}/email/callback/gmail"
        
        client_config = {
            "web": {
                "client_id": settings.gmail_client_id,
                "client_secret": settings.gmail_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [callback_url]
            }
        }
        
        flow = Flow.from_client_config(client_config, scopes=self.scopes)
        flow.redirect_uri = callback_url
        
        # Échanger le code contre des tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Obtenir l'adresse email de l'utilisateur
        service = build('gmail', 'v1', credentials=credentials)
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile['emailAddress']
        
        # Créer ou mettre à jour la connexion
        connection = self.db.query(EmailConnection).filter(
            EmailConnection.user_id == user_id,
            EmailConnection.provider == EmailProvider.GMAIL,
            EmailConnection.email_address == email_address
        ).first()
        
        if not connection:
            connection = EmailConnection(
                user_id=user_id,
                provider=EmailProvider.GMAIL,
                email_address=email_address
            )
            self.db.add(connection)
        
        connection.access_token = credentials.token
        connection.refresh_token = credentials.refresh_token
        connection.expires_at = credentials.expiry
        connection.status = ConnectionStatus.ACTIVE
        
        self.db.commit()
        self.db.refresh(connection)
        
        return connection

    def refresh_token(self, connection: EmailConnection) -> bool:
        """Rafraîchit le token d'accès"""
        try:
            credentials = Credentials(
                token=connection.access_token,
                refresh_token=connection.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.gmail_client_id,
                client_secret=settings.gmail_client_secret
            )
            
            credentials.refresh(GoogleRequest())
            
            connection.access_token = credentials.token
            connection.expires_at = credentials.expiry
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
            credentials = Credentials(
                token=connection.access_token,
                refresh_token=connection.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.gmail_client_id,
                client_secret=settings.gmail_client_secret
            )
            
            # Rafraîchir le token si expiré
            if credentials.expired and credentials.refresh_token:
                print(f"🔄 Gmail token expired for {connection.email_address}, refreshing...")
                try:
                    credentials.refresh(GoogleRequest())
                    connection.access_token = credentials.token
                    connection.expires_at = credentials.expiry
                    connection.status = ConnectionStatus.ACTIVE
                    self.db.commit()
                except Exception as e:
                    raise AuthenticationError(f"Failed to refresh token: {str(e)}")
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Construire la requête avec filtre de date si fourni
            query = 'in:inbox'
            if since_timestamp:
                # Gmail utilise le format: after:YYYY/MM/DD
                date_str = since_timestamp.strftime('%Y/%m/%d')
                query = f'in:inbox after:{date_str}'
            
            # Récupérer la liste des messages
            results = service.users().messages().list(
                userId='me',
                maxResults=max_results,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                # Récupérer le détail de chaque message
                msg = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                
                email_data = self._parse_gmail_message(msg)
                emails.append(email_data)
            
            print(f"✅ Fetched {len(emails)} Gmail emails for {connection.email_address}")
            return emails
            
        except HttpError as e:
            # Erreurs HTTP de l'API Gmail
            if e.resp.status == 401:
                error_msg = f"Authentication error: {str(e)}"
                print(f"🔐 {error_msg}")
                raise AuthenticationError(error_msg)
            else:
                error_msg = f"Gmail API error: {e.resp.status} - {str(e)}"
                print(f"⚠️ {error_msg}")
                raise Exception(error_msg)
                
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

    def get_emails_from_history(self, connection: EmailConnection, start_history_id: int) -> List[Dict[str, Any]]:
        """
        Récupère uniquement les NOUVEAUX emails depuis un history_id donné
        Utilise l'History API de Gmail pour une efficacité maximale
        """
        try:
            credentials = Credentials(
                token=connection.access_token,
                refresh_token=connection.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.gmail_client_id,
                client_secret=settings.gmail_client_secret
            )
            
            # Rafraîchir le token si expiré
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(GoogleRequest())
                connection.access_token = credentials.token
                connection.expires_at = credentials.expiry
                self.db.commit()
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Utiliser l'History API pour récupérer SEULEMENT les changements
            history_result = service.users().history().list(
                userId='me',
                startHistoryId=str(start_history_id),
                historyTypes=['messageAdded']  # Seulement les nouveaux messages
            ).execute()
            
            if 'history' not in history_result:
                print(f"📭 No new messages since history ID {start_history_id}")
                return []
            
            # Extraire les IDs des nouveaux messages
            new_message_ids = set()
            for history_record in history_result.get('history', []):
                for message_added in history_record.get('messagesAdded', []):
                    message = message_added.get('message', {})
                    # Filtrer uniquement les messages dans INBOX
                    if 'INBOX' in message.get('labelIds', []):
                        new_message_ids.add(message['id'])
            
            if not new_message_ids:
                print(f"📭 No new inbox messages in history")
                return []
            
            # Récupérer les détails de chaque nouveau message
            emails = []
            for msg_id in new_message_ids:
                msg = service.users().messages().get(
                    userId='me',
                    id=msg_id,
                    format='full'
                ).execute()
                
                email_data = self._parse_gmail_message(msg)
                emails.append(email_data)
            
            print(f"✅ Fetched {len(emails)} NEW emails from history for {connection.email_address}")
            return emails
            
        except HttpError as e:
            if e.resp.status == 404:
                # History ID trop ancien, fallback sur get_recent_emails
                print(f"⚠️ History ID {start_history_id} expired, falling back to recent emails")
                return self.get_recent_emails(connection, max_results=10)
            elif e.resp.status == 401:
                raise AuthenticationError(f"Authentication error: {str(e)}")
            else:
                raise Exception(f"Gmail API error: {e.resp.status} - {str(e)}")
        
        except Exception as e:
            print(f"❌ Error fetching history: {str(e)}")
            raise

    def _parse_gmail_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse un message Gmail"""
        headers = {h['name']: h['value'] for h in message['payload'].get('headers', [])}
        
        # Extraire le corps du message
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
        else:
            if message['payload']['body'].get('data'):
                body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
        
        # Parser la date RFC 2822 en datetime Python
        date_str = headers.get('Date', '')
        try:
            received_at = parsedate_to_datetime(date_str)
        except Exception as e:
            print(f"Error parsing date '{date_str}': {e}")
            received_at = datetime.now()
        
        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'sender_email': headers.get('From', '').split('<')[-1].rstrip('>') if '<' in headers.get('From', '') else headers.get('From', ''),
            'sender_name': headers.get('From', '').split('<')[0].strip() if '<' in headers.get('From', '') else '',
            'subject': headers.get('Subject', ''),
            'body': body,
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
        """Send email via Gmail API with optional attachments"""
        try:
            credentials = Credentials(
                token=connection.access_token,
                refresh_token=connection.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.gmail_client_id,
                client_secret=settings.gmail_client_secret
            )
            
            # Refresh token if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(GoogleRequest())
                connection.access_token = credentials.token
                connection.expires_at = credentials.expiry
                self.db.commit()
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Create message with attachments support
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            import os
            
            if attachments and len(attachments) > 0:
                # Use MIMEMultipart for attachments
                message = MIMEMultipart()
                message['to'] = to_email
                message['subject'] = subject
                
                # Add body
                message.attach(MIMEText(body, 'plain'))
                
                # Add attachments
                for attachment_info in attachments:
                    file_path = attachment_info['path']
                    filename = attachment_info['filename']
                    
                    with open(file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}'
                    )
                    message.attach(part)
                
                print(f"📎 Added {len(attachments)} attachment(s) to email")
            else:
                # Simple text message
                message = MIMEText(body)
                message['to'] = to_email
                message['subject'] = subject
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Send message
            send_result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"📧 Email sent via Gmail to {to_email}: {send_result.get('id')}")
            
            return {
                'success': True,
                'message_id': send_result.get('id'),
                'to': to_email
            }
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)