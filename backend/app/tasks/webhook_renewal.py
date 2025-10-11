"""
Celery tasks for webhook subscription renewal
"""
from app.celery_app import celery_app
from app.database.config import SessionLocal


@celery_app.task(name='app.tasks.webhook_renewal.renew_gmail_watches')
def renew_gmail_watches():
    """
    Periodic task: Renew Gmail watches that are expiring soon
    Should be executed once per day
    """
    db = SessionLocal()
    try:
        print("🔄 Starting Gmail watch renewal task...")
        
        from app.services.gmail_webhook_service import GmailWebhookService
        
        gmail_webhook = GmailWebhookService(db)
        result = gmail_webhook.check_and_renew_expiring_watches()
        
        print(f"✅ Gmail watch renewal completed: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Gmail watch renewal error: {str(e)}")
        return {'error': str(e)}
    finally:
        db.close()


@celery_app.task(name='app.tasks.webhook_renewal.renew_outlook_subscriptions')
def renew_outlook_subscriptions():
    """
    Periodic task: Renew Outlook subscriptions that are expiring soon
    Should be executed once per day
    """
    db = SessionLocal()
    try:
        print("🔄 Starting Outlook subscription renewal task...")
        
        from app.services.outlook_webhook_service import OutlookWebhookService
        
        outlook_webhook = OutlookWebhookService(db)
        result = outlook_webhook.check_and_renew_expiring_subscriptions()
        
        print(f"✅ Outlook subscription renewal completed: {result}")
        return result
        
    except Exception as e:
        print(f"❌ Outlook subscription renewal error: {str(e)}")
        return {'error': str(e)}
    finally:
        db.close()

