"""
Webhook endpoints for Gmail and Outlook push notifications
"""
from fastapi import APIRouter, Request, HTTPException, status, Header, Depends
from sqlalchemy.orm import Session
from typing import Optional
import json
import base64
import hmac
import hashlib
from datetime import datetime, timezone

from app.api.dependencies import get_db
from app.models.webhook_subscription import WebhookSubscription
from app.models.email_connection import EmailConnection
from app.services.gmail_webhook_service import GmailWebhookService
from app.services.outlook_webhook_service import OutlookWebhookService

router = APIRouter(prefix="/webhook", tags=["webhooks"])


@router.get("/gmail")
async def gmail_webhook_verify():
    """
    GET endpoint for Google Pub/Sub verification
    Google sends GET requests to verify the endpoint is valid
    """
    return {"status": "ok", "message": "Gmail webhook endpoint is ready"}


@router.post("/gmail")
async def gmail_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives push notifications from Google Cloud Pub/Sub
    
    Format: https://cloud.google.com/pubsub/docs/push
    """
    try:
        # Parse Pub/Sub message
        body = await request.json()
        
        if "message" not in body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Pub/Sub message format"
            )
        
        message = body["message"]
        
        # Decode message data (base64 encoded)
        if "data" in message:
            message_data = base64.b64decode(message["data"]).decode("utf-8")
            email_data = json.loads(message_data)
        else:
            email_data = {}
        
        print(f"📨 Gmail webhook received: {email_data}")
        
        # Extract email address and history ID from decoded data
        email_address = email_data.get("emailAddress")
        history_id = email_data.get("historyId")
        
        if not email_address:
            print(f"⚠️ No email address in Pub/Sub message. Full data: {email_data}")
            return {"status": "ignored", "reason": "no_email_address"}
        
        # Find connection
        connection = db.query(EmailConnection).filter(
            EmailConnection.email_address == email_address,
            EmailConnection.provider == "GMAIL"
        ).first()
        
        if not connection:
            print(f"⚠️ No connection found for {email_address}")
            return {"status": "ignored", "reason": "connection_not_found"}
        
        # Process notification using Gmail webhook service
        gmail_service = GmailWebhookService(db)
        result = gmail_service.process_notification(connection, history_id)
        
        return {
            "status": "success",
            "processed": result.get("synced", 0),
            "duplicates": result.get("duplicates", 0)
        }
        
    except Exception as e:
        print(f"❌ Gmail webhook error: {str(e)}")
        # Return 200 to avoid Pub/Sub retries
        return {"status": "error", "message": str(e)}


@router.post("/outlook/validation")
async def outlook_webhook_validation(
    request: Request,
    validationToken: Optional[str] = None
):
    """
    Microsoft Graph subscription validation endpoint
    
    When creating a subscription, Microsoft sends a validation request.
    We must respond with the validationToken in plain text.
    
    Docs: https://learn.microsoft.com/en-us/graph/webhooks#notification-endpoint-validation
    """
    if validationToken:
        print(f"✅ Outlook subscription validation: {validationToken[:20]}...")
        return validationToken
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No validation token provided"
    )


@router.post("/outlook")
async def outlook_webhook(
    request: Request,
    db: Session = Depends(get_db),
    client_state: Optional[str] = Header(None, alias="clientState"),
    validationToken: Optional[str] = None
):
    """
    Receives webhook notifications from Microsoft Graph API
    
    Format: https://learn.microsoft.com/en-us/graph/webhooks#processing-the-change-notification
    """
    try:
        # Handle validation request (Microsoft sends this as query parameter)
        if validationToken:
            print(f"✅ Outlook validation request received: {validationToken[:20]}...")
            # Must respond with plain text validation token
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(content=validationToken, status_code=200)
        
        body = await request.json()
        
        # Handle validation request (alternative method)
        if "validationToken" in body:
            return {"validationToken": body["validationToken"]}
        
        # Process change notifications
        if "value" not in body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid notification format"
            )
        
        print(f"📨 Outlook webhook received: {len(body['value'])} notifications")
        
        outlook_service = OutlookWebhookService(db)
        results = []
        
        for notification in body["value"]:
            subscription_id = notification.get("subscriptionId")
            resource = notification.get("resource")
            change_type = notification.get("changeType")
            
            print(f"📬 Notification: subscription={subscription_id}, change={change_type}")
            
            # Find subscription
            subscription = db.query(WebhookSubscription).filter(
                WebhookSubscription.subscription_id == subscription_id,
                WebhookSubscription.provider == "OUTLOOK"
            ).first()
            
            if not subscription:
                print(f"⚠️ Subscription not found: {subscription_id}")
                results.append({"status": "ignored", "reason": "subscription_not_found"})
                continue
            
            # Validate client state
            notification_client_state = notification.get("clientState")
            if notification_client_state != subscription.client_state:
                print(f"⚠️ Invalid client state for subscription {subscription_id}")
                results.append({"status": "ignored", "reason": "invalid_client_state"})
                continue
            
            # Get connection
            connection = db.query(EmailConnection).filter(
                EmailConnection.id == subscription.connection_id
            ).first()
            
            if not connection:
                print(f"⚠️ Connection not found for subscription {subscription_id}")
                results.append({"status": "ignored", "reason": "connection_not_found"})
                continue
            
            # Process notification
            if change_type == "created":
                result = outlook_service.process_notification(connection, resource)
                results.append(result)
            else:
                print(f"ℹ️ Ignoring change type: {change_type}")
                results.append({"status": "ignored", "reason": f"change_type_{change_type}"})
        
        return {
            "status": "success",
            "processed": len([r for r in results if r.get("status") == "success"]),
            "ignored": len([r for r in results if r.get("status") == "ignored"])
        }
        
    except Exception as e:
        print(f"❌ Outlook webhook error: {str(e)}")
        # Return 200 to avoid Microsoft retries
        return {"status": "error", "message": str(e)}


@router.get("/status")
def get_webhook_status(db: Session = Depends(get_db)):
    """
    Get status of all webhook subscriptions (for monitoring)
    """
    subscriptions = db.query(WebhookSubscription).all()
    
    return {
        "total": len(subscriptions),
        "active": len([s for s in subscriptions if s.status == "active"]),
        "expired": len([s for s in subscriptions if s.status == "expired"]),
        "subscriptions": [
            {
                "id": s.id,
                "provider": s.provider,
                "status": s.status,
                "expires_at": s.expires_at.isoformat(),
                "notification_count": s.notification_count,
                "last_notification_at": s.last_notification_at.isoformat() if s.last_notification_at else None
            }
            for s in subscriptions
        ]
    }

