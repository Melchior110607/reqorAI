"""
Outlook Webhook Service - Manages Microsoft Graph webhook subscriptions
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import os
import secrets
import requests

from app.models.email_connection import EmailConnection
from app.models.webhook_subscription import WebhookSubscription
from app.services.outlook_service import OutlookService


class OutlookWebhookService:
    """Service for managing Outlook webhook subscriptions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.outlook_service = OutlookService(db)
        self.tenant_id = os.getenv("OUTLOOK_TENANT_ID")
        self.webhook_base_url = os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000")
        
        if not self.tenant_id:
            raise ValueError("OUTLOOK_TENANT_ID not configured in environment")
    
    def create_subscription(self, connection: EmailConnection) -> Dict[str, Any]:
        """
        Create a Microsoft Graph webhook subscription
        
        Docs: https://learn.microsoft.com/en-us/graph/webhooks
        
        Subscriptions expire after max 3 days (4230 minutes)
        """
        try:
            print(f"🔔 Creating Outlook subscription for {connection.email_address}")
            
            # Generate a secret client state for validation
            client_state = secrets.token_urlsafe(32)
            
            # Subscription expires in 3 days (max allowed)
            expires_at = datetime.now(timezone.utc) + timedelta(days=3)
            expiration_datetime = expires_at.strftime("%Y-%m-%dT%H:%M:%S.0000000Z")
            
            # Subscription payload
            subscription_payload = {
                "changeType": "created",
                "notificationUrl": f"{self.webhook_base_url}/webhook/outlook",
                "resource": "/me/mailFolders('inbox')/messages",
                "expirationDateTime": expiration_datetime,
                "clientState": client_state
            }
            
            # Create subscription
            headers = {
                "Authorization": f"Bearer {connection.access_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                "https://graph.microsoft.com/v1.0/subscriptions",
                json=subscription_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                subscription_data = response.json()
                subscription_id = subscription_data.get("id")
                
                print(f"✅ Outlook subscription created: {subscription_id}")
                
                # Save to database
                db_subscription = self.db.query(WebhookSubscription).filter(
                    WebhookSubscription.connection_id == connection.id,
                    WebhookSubscription.provider == "OUTLOOK"
                ).first()
                
                if db_subscription:
                    # Update existing
                    db_subscription.subscription_id = subscription_id
                    db_subscription.resource = subscription_data.get("resource")
                    db_subscription.client_state = client_state
                    db_subscription.expires_at = expires_at
                    db_subscription.status = 'active'
                    db_subscription.last_error = None
                    db_subscription.updated_at = datetime.now(timezone.utc)
                else:
                    # Create new
                    db_subscription = WebhookSubscription(
                        connection_id=connection.id,
                        provider="OUTLOOK",
                        subscription_id=subscription_id,
                        resource=subscription_data.get("resource"),
                        client_state=client_state,
                        expires_at=expires_at,
                        status='active'
                    )
                    self.db.add(db_subscription)
                
                self.db.commit()
                
                # 🔄 Obtenir le deltaLink initial pour Outlook
                # Cela permet de ne récupérer que les NOUVEAUX emails lors des prochains webhooks
                # Note: Il faut suivre tous les @odata.nextLink jusqu'à obtenir @odata.deltaLink
                # Astuce: Utiliser $top=1 pour minimiser les données et accélérer l'obtention du deltaLink
                try:
                    delta_url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages/delta?$top=1"
                    delta_link = None
                    max_iterations = 50  # Protection contre boucle infinie (augmenté pour gros inbox)
                    iteration = 0
                    
                    # Headers avec préférence pour réduire la taille des pages
                    delta_headers = headers.copy()
                    delta_headers['Prefer'] = 'odata.maxpagesize=1'
                    
                    while delta_url and iteration < max_iterations:
                        delta_response = requests.get(delta_url, headers=delta_headers, timeout=30)
                        
                        if delta_response.status_code == 200:
                            delta_data = delta_response.json()
                            
                            # Debug: afficher les clés de la réponse
                            response_keys = list(delta_data.keys())
                            print(f"📋 Response keys: {response_keys}")
                            
                            # Vérifier si on a le deltaLink final
                            if '@odata.deltaLink' in delta_data:
                                delta_link = delta_data['@odata.deltaLink']
                                print(f"✅ Delta link obtained after {iteration + 1} iteration(s)")
                                break
                            
                            # Sinon, suivre le nextLink
                            if '@odata.nextLink' in delta_data:
                                delta_url = delta_data['@odata.nextLink']
                                iteration += 1
                                print(f"🔄 Following nextLink (iteration {iteration})...")
                            else:
                                # Vérifier s'il y a un skipToken (autre format de pagination)
                                if any('@odata.next' in k for k in response_keys):
                                    print(f"⚠️ Found alternate next key: {[k for k in response_keys if 'next' in k.lower()]}")
                                print(f"⚠️ No deltaLink or nextLink in response (got {len(delta_data.get('value', []))} messages)")
                                break
                        else:
                            print(f"⚠️ Failed to get delta link: {delta_response.status_code}")
                            break
                    
                    if delta_link:
                        # Sauvegarder le deltaLink avec préfixe 'delta:'
                        db_subscription.resource = f"delta:{delta_link}"
                        self.db.commit()
                        print(f"✅ Delta link initialized for Outlook")
                    else:
                        print(f"⚠️ Could not obtain deltaLink, will use recent emails fallback")
                
                except Exception as delta_error:
                    print(f"⚠️ Failed to initialize delta link (non-critical): {str(delta_error)}")
                
                print(f"✅ Webhook subscription saved (expires: {expires_at})")
                
                return {
                    "success": True,
                    "subscription_id": subscription_id,
                    "expires_at": expires_at.isoformat()
                }
            
            elif response.status_code == 401:
                error_msg = "Authentication error - token may be expired"
                print(f"❌ {error_msg}")
                
                # Mark subscription as failed
                db_subscription = self.db.query(WebhookSubscription).filter(
                    WebhookSubscription.connection_id == connection.id,
                    WebhookSubscription.provider == "OUTLOOK"
                ).first()
                
                if db_subscription:
                    db_subscription.status = 'failed'
                    db_subscription.last_error = error_msg
                    self.db.commit()
                
                raise Exception(error_msg)
            
            else:
                error_msg = f"Failed to create subscription: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def delete_subscription(self, connection: EmailConnection) -> Dict[str, Any]:
        """
        Delete a Microsoft Graph webhook subscription
        """
        try:
            print(f"🛑 Deleting Outlook subscription for {connection.email_address}")
            
            # Get subscription from database
            subscription = self.db.query(WebhookSubscription).filter(
                WebhookSubscription.connection_id == connection.id,
                WebhookSubscription.provider == "OUTLOOK"
            ).first()
            
            if not subscription or not subscription.subscription_id:
                print("⚠️ No subscription found")
                return {"success": True, "message": "No subscription to delete"}
            
            # Delete from Microsoft Graph
            headers = {
                "Authorization": f"Bearer {connection.access_token}"
            }
            
            response = requests.delete(
                f"https://graph.microsoft.com/v1.0/subscriptions/{subscription.subscription_id}",
                headers=headers,
                timeout=30
            )
            
            # Update database (mark as expired)
            subscription.status = 'expired'
            self.db.commit()
            
            if response.status_code == 204:
                print(f"✅ Outlook subscription deleted")
                return {"success": True}
            else:
                print(f"⚠️ Delete returned {response.status_code}, but marked as expired in DB")
                return {"success": True, "warning": f"Status {response.status_code}"}
            
        except Exception as e:
            print(f"❌ Error deleting subscription: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def process_notification(self, connection: EmailConnection, resource: str) -> Dict[str, Any]:
        """
        Process an Outlook webhook notification
        
        When we receive a notification about a new email, fetch it and store it.
        
        Args:
            connection: Email connection
            resource: Resource path from notification (e.g., "/me/messages/AAMk...")
        
        Returns:
            dict: Processing result
        """
        try:
            print(f"📬 Processing Outlook notification for {connection.email_address}")
            print(f"📄 Resource: {resource}")
            
            # Get subscription
            subscription = self.db.query(WebhookSubscription).filter(
                WebhookSubscription.connection_id == connection.id,
                WebhookSubscription.provider == "OUTLOOK"
            ).first()
            
            if not subscription:
                print(f"⚠️ No subscription found for connection {connection.id}")
                return {"status": "ignored", "reason": "no_subscription"}
            
            # Use Outlook Delta API to fetch ONLY new emails since last deltaLink
            emails = []
            new_delta_link = None
            
            if subscription.resource and subscription.resource.startswith('delta:'):
                # Utiliser deltaLink pour récupérer seulement les changements
                delta_link = subscription.resource.replace('delta:', '')
                
                # get_emails_from_delta devrait retourner (emails, new_delta_link)
                # Pour l'instant on l'appelle et on récupère juste les emails
                try:
                    # Faire l'appel Delta manuellement pour récupérer le nouveau deltaLink
                    headers = {'Authorization': f'Bearer {connection.access_token}'}
                    response = requests.get(delta_link, headers=headers, timeout=30)
                    
                    if response.status_code == 200:
                        delta_data = response.json()
                        
                        # Récupérer les nouveaux emails
                        for msg in delta_data.get('value', []):
                            if '@removed' not in msg:  # Ignorer les emails supprimés
                                email_data = self.outlook_service._parse_outlook_message(msg)
                                emails.append(email_data)
                        
                        # Récupérer le nouveau deltaLink pour la prochaine fois
                        new_delta_link = delta_data.get('@odata.deltaLink')
                        
                        if new_delta_link:
                            print(f"🔄 Updated delta link for next sync")
                        else:
                            print(f"⚠️ No new delta link in response")
                    
                    else:
                        print(f"⚠️ Delta API error: {response.status_code}, falling back")
                        emails = self.outlook_service.get_recent_emails(connection, max_results=10)
                
                except Exception as delta_error:
                    print(f"⚠️ Delta fetch error: {str(delta_error)}, falling back")
                    emails = self.outlook_service.get_recent_emails(connection, max_results=10)
            else:
                # Premier webhook, récupérer emails récents
                print(f"📥 No delta link yet, fetching recent emails")
                emails = self.outlook_service.get_recent_emails(
                    connection=connection,
                    max_results=10,
                    since_timestamp=connection.last_sync
                )
            
            # Process and save the emails to database
            from app.services.email_service import EmailProcessingService
            processing_service = EmailProcessingService(self.db)
            
            synced = 0
            duplicates = 0
            
            for email_data in emails:
                result = processing_service.process_intercepted_email(
                    email_data,
                    connection.id,
                    connection.user_id
                )
                if result:
                    synced += 1
                else:
                    duplicates += 1
            
            # Update subscription metadata
            subscription.last_notification_at = datetime.now(timezone.utc)
            subscription.notification_count += 1
            
            # Sauvegarder le nouveau deltaLink s'il existe
            if new_delta_link:
                subscription.resource = f"delta:{new_delta_link}"
                print(f"💾 Saved new delta link for future syncs")
            
            self.db.commit()
            
            print(f"✅ Notification processed: {synced} emails saved, {duplicates} duplicates")
            
            return {
                "status": "success",
                "synced": synced,
                "duplicates": duplicates
            }
            
        except Exception as e:
            error_msg = f"Error processing notification: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Update subscription error
            subscription = self.db.query(WebhookSubscription).filter(
                WebhookSubscription.connection_id == connection.id,
                WebhookSubscription.provider == "OUTLOOK"
            ).first()
            
            if subscription:
                subscription.last_error = error_msg
                self.db.commit()
            
            return {"status": "error", "message": str(e)}
    
    def renew_subscription(self, connection: EmailConnection) -> Dict[str, Any]:
        """
        Renew an Outlook subscription
        
        Microsoft Graph subscriptions expire after max 3 days.
        We need to PATCH the subscription with a new expiration date.
        """
        try:
            print(f"🔄 Renewing Outlook subscription for {connection.email_address}")
            
            # Get subscription from database
            subscription = self.db.query(WebhookSubscription).filter(
                WebhookSubscription.connection_id == connection.id,
                WebhookSubscription.provider == "OUTLOOK"
            ).first()
            
            if not subscription or not subscription.subscription_id:
                print("⚠️ No subscription found, creating new one")
                return self.create_subscription(connection)
            
            # New expiration (3 days from now)
            expires_at = datetime.now(timezone.utc) + timedelta(days=3)
            expiration_datetime = expires_at.strftime("%Y-%m-%dT%H:%M:%S.0000000Z")
            
            # Update subscription
            headers = {
                "Authorization": f"Bearer {connection.access_token}",
                "Content-Type": "application/json"
            }
            
            patch_payload = {
                "expirationDateTime": expiration_datetime
            }
            
            response = requests.patch(
                f"https://graph.microsoft.com/v1.0/subscriptions/{subscription.subscription_id}",
                json=patch_payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                subscription_data = response.json()
                
                print(f"✅ Outlook subscription renewed: {subscription.subscription_id}")
                
                # Update database
                subscription.expires_at = expires_at
                subscription.status = 'active'
                subscription.last_error = None
                subscription.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                
                return {
                    "success": True,
                    "subscription_id": subscription.subscription_id,
                    "expires_at": expires_at.isoformat()
                }
            
            elif response.status_code == 404:
                # Subscription doesn't exist anymore, create new one
                print("⚠️ Subscription not found on Microsoft Graph, creating new one")
                return self.create_subscription(connection)
            
            else:
                error_msg = f"Failed to renew subscription: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                
                subscription.status = 'failed'
                subscription.last_error = error_msg
                self.db.commit()
                
                raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def check_and_renew_expiring_subscriptions(self) -> Dict[str, Any]:
        """
        Check all Outlook subscriptions and renew those expiring soon
        
        Should be called by Celery Beat every day.
        """
        print("🔍 Checking for expiring Outlook subscriptions...")
        
        # Find subscriptions expiring in next 24 hours
        threshold = datetime.now(timezone.utc) + timedelta(hours=24)
        
        expiring = self.db.query(WebhookSubscription).filter(
            WebhookSubscription.provider == "OUTLOOK",
            WebhookSubscription.status == "active",
            WebhookSubscription.expires_at < threshold
        ).all()
        
        print(f"📋 Found {len(expiring)} expiring subscriptions")
        
        renewed = 0
        failed = 0
        
        for subscription in expiring:
            connection = self.db.query(EmailConnection).filter(
                EmailConnection.id == subscription.connection_id
            ).first()
            
            if not connection:
                print(f"⚠️ Connection not found for subscription {subscription.id}")
                continue
            
            try:
                self.renew_subscription(connection)
                renewed += 1
                print(f"✅ Renewed subscription for {connection.email_address}")
            except Exception as e:
                failed += 1
                print(f"❌ Failed to renew subscription for {connection.email_address}: {str(e)}")
        
        return {
            "checked": len(expiring),
            "renewed": renewed,
            "failed": failed
        }

