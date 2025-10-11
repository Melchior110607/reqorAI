"""
Debug endpoints - TEMPORARY, REMOVE IN PRODUCTION
"""
from fastapi import APIRouter, Depends, Request
from app.models.user import User
from app.models.email_connection import EmailConnection
from app.models.webhook_subscription import WebhookSubscription
from app.api.dependencies import get_current_user
from app.database.config import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/connections")
def list_all_connections(db: Session = Depends(get_db)):
    """
    ⚠️ DEBUG ONLY - Lists ALL email connections (no auth required)
    """
    connections = db.query(EmailConnection).all()
    
    return {
        "total": len(connections),
        "connections": [
            {
                "id": conn.id,
                "user_id": conn.user_id,
                "provider": conn.provider.value,
                "email_address": conn.email_address,
                "status": conn.status.value,
                "has_webhook": db.query(WebhookSubscription).filter(
                    WebhookSubscription.connection_id == conn.id
                ).first() is not None
            }
            for conn in connections
        ],
        "instructions": {
            "1": "Find your Gmail connection ID above",
            "2": "Get your token: Open http://localhost:3000, press F12, go to Application tab > Local Storage > copy 'token' value",
            "3": "Run: curl -X POST http://localhost:8000/email/webhook/setup/CONNECTION_ID -H 'Authorization: Bearer YOUR_TOKEN'",
            "4": "Alternative: Use /debug/setup endpoint below"
        }
    }


@router.get("/me")
def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    ⚠️ DEBUG ONLY - Shows current user info and connections (requires auth)
    """
    connections = db.query(EmailConnection).filter(
        EmailConnection.user_id == current_user.id
    ).all()
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "company": current_user.company
        },
        "connections": [
            {
                "id": conn.id,
                "provider": conn.provider.value,
                "email_address": conn.email_address,
                "status": conn.status.value
            }
            for conn in connections
        ],
        "instructions": {
            "setup_gmail_webhook": f"curl -X POST http://localhost:8000/email/webhook/setup/CONNECTION_ID -H 'Authorization: Bearer YOUR_TOKEN'",
            "note": "Replace CONNECTION_ID with the Gmail connection id above"
        }
    }


@router.get("/token-info")
def get_token_info(current_user: User = Depends(get_current_user)):
    """
    ⚠️ DEBUG ONLY - Shows info about your authentication
    """
    return {
        "message": "You are authenticated!",
        "user_id": current_user.id,
        "email": current_user.email,
        "note": "Your token is valid. Use it in the Authorization header: 'Bearer YOUR_TOKEN'"
    }

