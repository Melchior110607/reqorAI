"""
Gmail Webhook Service - Manages Gmail push notifications via Pub/Sub
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import os
import secrets

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.models.email_connection import EmailConnection
from app.models.webhook_subscription import WebhookSubscription
from app.services.gmail_service import GmailService


class GmailWebhookService:
    """Service for managing Gmail push notifications"""
    
    def __init__(self, db: Session):
        self.db = db
        self.gmail_service = GmailService(db)
        self.topic_name = os.getenv("GMAIL_PUBSUB_TOPIC")
        
        if not self.topic_name:
            raise ValueError("GMAIL_PUBSUB_TOPIC not configured in environment")
    
    def setup_watch(self, connection: EmailConnection) -> Dict[str, Any]:
        """
        Setup Gmail push notifications (watch) for a connection
        
        Gmail watch expires after 7 days, so we need to renew it.
        
        Returns:
            dict: Watch response with historyId and expiration
        """
        try:
            print(f"🔔 Setting up Gmail watch for {connection.email_address}")
            
            # Build Gmail service
            credentials = Credentials(
                token=connection.access_token,
                refresh_token=connection.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GMAIL_CLIENT_ID"),
                client_secret=os.getenv("GMAIL_CLIENT_SECRET")
            )
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Call watch API
            watch_request = {
                'topicName': self.topic_name,
                'labelIds': ['INBOX']  # Watch only inbox
            }
            
            watch_response = service.users().watch(
                userId='me',
                body=watch_request
            ).execute()
            
            print(f"✅ Gmail watch setup successful: {watch_response}")
            
            history_id = int(watch_response.get('historyId'))
            expiration = int(watch_response.get('expiration'))  # Unix timestamp in milliseconds
            expires_at = datetime.fromtimestamp(expiration / 1000, tz=timezone.utc)
            
            # Create or update webhook subscription
            subscription = self.db.query(WebhookSubscription).filter(
                WebhookSubscription.connection_id == connection.id,
                WebhookSubscription.provider == "GMAIL"
            ).first()
            
            if subscription:
                # Update existing
                subscription.topic_name = self.topic_name
                subscription.history_id = history_id
                subscription.expires_at = expires_at
                subscription.status = 'active'
                subscription.last_error = None
                subscription.updated_at = datetime.now(timezone.utc)
            else:
                # Create new
                subscription = WebhookSubscription(
                    connection_id=connection.id,
                    provider="GMAIL",
                    topic_name=self.topic_name,
                    history_id=history_id,
                    expires_at=expires_at,
                    status='active'
                )
                self.db.add(subscription)
            
            self.db.commit()
            
            print(f"✅ Webhook subscription saved (expires: {expires_at})")
            
            return {
                "success": True,
                "history_id": history_id,
                "expires_at": expires_at.isoformat()
            }
            
        except HttpError as e:
            error_msg = f"Gmail API error: {e.resp.status} - {str(e)}"
            print(f"❌ {error_msg}")
            
            # Update subscription status
            subscription = self.db.query(WebhookSubscription).filter(
                WebhookSubscription.connection_id == connection.id,
                WebhookSubscription.provider == "GMAIL"
            ).first()
            
            if subscription:
                subscription.status = 'failed'
                subscription.last_error = error_msg
                self.db.commit()
            
            raise Exception(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def stop_watch(self, connection: EmailConnection) -> Dict[str, Any]:
        """
        Stop Gmail push notifications for a connection
        """
        try:
            print(f"🛑 Stopping Gmail watch for {connection.email_address}")
            
            credentials = Credentials(
                token=connection.access_token,
                refresh_token=connection.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=os.getenv("GMAIL_CLIENT_ID"),
                client_secret=os.getenv("GMAIL_CLIENT_SECRET")
            )
            
            service = build('gmail', 'v1', credentials=credentials)
            
            # Call stop API
            service.users().stop(userId='me').execute()
            
            # Update subscription status
            subscription = self.db.query(WebhookSubscription).filter(
                WebhookSubscription.connection_id == connection.id,
                WebhookSubscription.provider == "GMAIL"
            ).first()
            
            if subscription:
                subscription.status = 'expired'
                self.db.commit()
            
            print(f"✅ Gmail watch stopped")
            
            return {"success": True}
            
        except Exception as e:
            print(f"❌ Error stopping watch: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def process_notification(self, connection: EmailConnection, history_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Process a Gmail push notification
        
        When we receive a notification, we need to fetch the history since last historyId
        and process new emails.
        
        Args:
            connection: Email connection
            history_id: New history ID from notification
        
        Returns:
            dict: Processing result with synced/duplicate counts
        """
        try:
            print(f"📬 Processing Gmail notification for {connection.email_address}")
            
            # Get subscription
            subscription = self.db.query(WebhookSubscription).filter(
                WebhookSubscription.connection_id == connection.id,
                WebhookSubscription.provider == "GMAIL"
            ).first()
            
            if not subscription:
                print(f"⚠️ No subscription found for connection {connection.id}")
                return {"synced": 0, "duplicates": 0}
            
            # Use Gmail service to fetch recent emails
            # We'll fetch emails since last_sync (or last 10 emails if no last_sync)
            result = self.gmail_service.get_recent_emails(
                connection=connection,
                max_results=10,
                since_timestamp=connection.last_sync
            )
            
            # Update subscription metadata
            subscription.last_notification_at = datetime.now(timezone.utc)
            subscription.notification_count += 1
            
            if history_id:
                subscription.history_id = history_id
            
            self.db.commit()
            
            print(f"✅ Notification processed: {len(result)} emails fetched")
            
            return {
                "synced": len(result),
                "duplicates": 0  # GmailService handles duplicates
            }
            
        except Exception as e:
            error_msg = f"Error processing notification: {str(e)}"
            print(f"❌ {error_msg}")
            
            # Update subscription error
            subscription = self.db.query(WebhookSubscription).filter(
                WebhookSubscription.connection_id == connection.id,
                WebhookSubscription.provider == "GMAIL"
            ).first()
            
            if subscription:
                subscription.last_error = error_msg
                self.db.commit()
            
            raise Exception(error_msg)
    
    def renew_watch(self, connection: EmailConnection) -> Dict[str, Any]:
        """
        Renew Gmail watch (same as setup_watch)
        
        Gmail watch expires after 7 days, so we need to renew it periodically.
        """
        print(f"🔄 Renewing Gmail watch for {connection.email_address}")
        return self.setup_watch(connection)
    
    def check_and_renew_expiring_watches(self) -> Dict[str, Any]:
        """
        Check all Gmail subscriptions and renew those expiring soon
        
        Should be called by Celery Beat every day.
        """
        print("🔍 Checking for expiring Gmail watches...")
        
        # Find subscriptions expiring in next 24 hours
        threshold = datetime.now(timezone.utc) + timedelta(hours=24)
        
        expiring = self.db.query(WebhookSubscription).filter(
            WebhookSubscription.provider == "GMAIL",
            WebhookSubscription.status == "active",
            WebhookSubscription.expires_at < threshold
        ).all()
        
        print(f"📋 Found {len(expiring)} expiring watches")
        
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
                self.renew_watch(connection)
                renewed += 1
                print(f"✅ Renewed watch for {connection.email_address}")
            except Exception as e:
                failed += 1
                print(f"❌ Failed to renew watch for {connection.email_address}: {str(e)}")
        
        return {
            "checked": len(expiring),
            "renewed": renewed,
            "failed": failed
        }

