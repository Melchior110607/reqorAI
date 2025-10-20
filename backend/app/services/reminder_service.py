"""
Reminder Service - Auto-send reminders for outgoing requests
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
import openai

from app.models.request import Request, RequestStatus, RequestType, ReminderFrequency
from app.models.email_connection import EmailConnection
from app.models.client import Client
from app.services.gmail_service import GmailService
from app.services.outlook_service import OutlookService
from app.database.config import settings


class ReminderService:
    def __init__(self, db: Session):
        self.db = db
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
    
    def should_send_reminder(self, request: Request) -> bool:
        """
        Determine if a reminder should be sent for this request
        """
        # Only for outgoing requests
        if request.type != RequestType.OUTGOING:
            return False
        
        # Only if reminder is enabled
        if not request.reminder_enabled:
            return False
        
        # Only if request is not completed
        if request.status == RequestStatus.COMPLETED:
            return False
        
        # Check frequency
        if request.reminder_frequency == ReminderFrequency.NEVER:
            return False
        
        # Check if enough time has passed since last reminder
        now = datetime.now(timezone.utc)
        
        # If never sent, check if request is old enough (wait at least 1 day)
        if request.last_reminder_sent_at is None:
            days_since_creation = (now - request.created_at).days
            return days_since_creation >= 1
        
        # Calculate next send time based on frequency
        days_since_last = (now - request.last_reminder_sent_at).days
        
        frequency_days = {
            ReminderFrequency.DAILY: 1,
            ReminderFrequency.WEEKLY: 7,
            ReminderFrequency.BIWEEKLY: 14,
            ReminderFrequency.MONTHLY: 30
        }
        
        required_days = frequency_days.get(request.reminder_frequency, 999)
        return days_since_last >= required_days
    
    def send_reminder(self, request: Request) -> Dict[str, Any]:
        """
        Send a reminder email for the given request
        """
        try:
            print(f"📧 Sending reminder for request {request.id}: {request.title}")
            
            # Get client
            client = self.db.query(Client).filter(Client.id == request.client_id).first()
            if not client:
                return {"success": False, "error": "Client not found"}
            
            # Get email connection
            if not request.email_connection_id:
                return {"success": False, "error": "No email connection associated"}
            
            connection = self.db.query(EmailConnection).filter(
                EmailConnection.id == request.email_connection_id
            ).first()
            
            if not connection:
                return {"success": False, "error": "Email connection not found"}
            
            # Use user's custom message or default template
            if request.reminder_message:
                reminder_body = request.reminder_message
            else:
                # Simple default template without AI
                reminder_body = f"""Hello,

This is a friendly reminder regarding: "{request.title}".

We would appreciate an update when you have a chance.

Thank you!"""
            
            # Send email based on provider
            if connection.provider.value == "gmail":
                gmail_service = GmailService(self.db)
                result = gmail_service.send_email(
                    connection=connection,
                    to_email=client.email,
                    subject=f"Reminder: {request.title}",
                    body=reminder_body
                )
            elif connection.provider.value == "outlook":
                outlook_service = OutlookService(self.db)
                result = outlook_service.send_email(
                    connection=connection,
                    to_email=client.email,
                    subject=f"Reminder: {request.title}",
                    body=reminder_body
                )
            else:
                return {"success": False, "error": f"Unsupported provider: {connection.provider}"}
            
            # Update request
            request.last_reminder_sent_at = datetime.now(timezone.utc)
            request.reminder_count += 1
            self.db.commit()
            
            print(f"✅ Reminder sent! Count: {request.reminder_count}")
            
            return {
                "success": True,
                "request_id": request.id,
                "reminder_count": request.reminder_count,
                "sent_to": client.email
            }
            
        except Exception as e:
            error_msg = f"Failed to send reminder: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    
    def process_pending_reminders(self) -> Dict[str, Any]:
        """
        Process all pending reminders
        
        Called by Celery beat task.
        """
        print("🔔 Processing pending reminders...")
        
        # Get all outgoing requests with reminders enabled
        requests_with_reminders = self.db.query(Request).filter(
            Request.type == RequestType.OUTGOING,
            Request.reminder_enabled == True,
            Request.status != RequestStatus.COMPLETED
        ).all()
        
        print(f"📋 Found {len(requests_with_reminders)} requests with reminders enabled")
        
        sent_count = 0
        skipped_count = 0
        failed_count = 0
        
        for request in requests_with_reminders:
            if self.should_send_reminder(request):
                result = self.send_reminder(request)
                if result.get("success"):
                    sent_count += 1
                else:
                    failed_count += 1
                    print(f"⚠️ Failed to send reminder for request {request.id}: {result.get('error')}")
            else:
                skipped_count += 1
        
        summary = {
            "checked": len(requests_with_reminders),
            "sent": sent_count,
            "skipped": skipped_count,
            "failed": failed_count
        }
        
        print(f"✅ Reminder processing complete: {summary}")
        return summary

