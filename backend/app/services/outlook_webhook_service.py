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
            
            # Use Outlook service to fetch recent emails
            # Since we get notified in real-time, we just fetch the latest emails
            result = self.outlook_service.get_recent_emails(
                connection=connection,
                max_results=5,  # Just fetch a few latest
                since_timestamp=connection.last_sync
            )
            
            # Update subscription metadata
            subscription.last_notification_at = datetime.now(timezone.utc)
            subscription.notification_count += 1
            self.db.commit()
            
            print(f"✅ Notification processed: {len(result)} emails fetched")
            
            return {
                "status": "success",
                "synced": len(result),
                "duplicates": 0
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

