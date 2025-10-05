from fastapi import APIRouter, Depends, HTTPException, status, Request as FastAPIRequest
from sqlalchemy.orm import Session
from typing import List
import json
from app.database.config import get_db
from app.schemas.email import (
    EmailConnectionResponse, 
    InterceptedEmailResponse, 
    InterceptedEmailWithClient,
    AuthUrlResponse,
    OAuthCallbackRequest,
    EmailClassificationRequest,
    EmailClassificationResponse
)
from app.models.email_connection import EmailConnection, EmailProvider
from app.models.intercepted_email import InterceptedEmail
from app.models.client import Client
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.gmail_service import GmailService
from app.services.outlook_service import OutlookService
from app.services.email_service import EmailProcessingService
from app.services.ai_service import AIClassificationService

router = APIRouter(prefix="/email", tags=["Email Integration"])

@router.get("/auth-url/{provider}", response_model=AuthUrlResponse)
def get_auth_url(
    provider: EmailProvider,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtient l'URL d'authentification pour un provider"""
    try:
        if provider == EmailProvider.GMAIL:
            gmail_service = GmailService(db)
            auth_url = gmail_service.get_auth_url(current_user.id)
        elif provider == EmailProvider.OUTLOOK:
            outlook_service = OutlookService(db)
            auth_url = outlook_service.get_auth_url(current_user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported email provider"
            )
        
        return AuthUrlResponse(auth_url=auth_url, provider=provider)
        
    except Exception as e:
        print(f"Error generating auth URL for {provider}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate auth URL for {provider}: {str(e)}"
        )

@router.get("/callback/{provider}")
def oauth_callback(
    provider: EmailProvider,
    code: str,
    state: str,
    error: str = None,
    db: Session = Depends(get_db)
):
    """Gère le callback OAuth"""
    from fastapi.responses import RedirectResponse
    
    if error:
        # Rediriger vers la page de callback avec l'erreur
        return RedirectResponse(url=f"http://localhost:3000/email-callback?error={error}")
    
    try:
        if provider == EmailProvider.GMAIL:
            gmail_service = GmailService(db)
            connection = gmail_service.handle_oauth_callback(code, state)
        elif provider == EmailProvider.OUTLOOK:
            outlook_service = OutlookService(db)
            connection = outlook_service.handle_oauth_callback(code, state)
        else:
            return RedirectResponse(url="http://localhost:3000/email-callback?error=unsupported_provider")
        
        # Rediriger vers la page de callback avec succès
        return RedirectResponse(url=f"http://localhost:3000/email-callback?success=true&provider={provider}")
        
    except Exception as e:
        print(f"OAuth callback error: {str(e)}")
        return RedirectResponse(url=f"http://localhost:3000/email-callback?error={str(e)}")

@router.get("/connections", response_model=List[EmailConnectionResponse])
def get_email_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les connexions email de l'utilisateur"""
    connections = db.query(EmailConnection).filter(
        EmailConnection.user_id == current_user.id
    ).all()
    
    return connections

@router.delete("/connections/{connection_id}")
def delete_email_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprime une connexion email"""
    connection = db.query(EmailConnection).filter(
        EmailConnection.id == connection_id,
        EmailConnection.user_id == current_user.id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email connection not found"
        )
    
    db.delete(connection)
    db.commit()
    
    return {"message": "Email connection deleted successfully"}

@router.post("/sync/{connection_id}")
def sync_emails(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Synchronise les emails d'une connexion"""
    connection = db.query(EmailConnection).filter(
        EmailConnection.id == connection_id,
        EmailConnection.user_id == current_user.id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email connection not found"
        )
    
    try:
        if connection.provider == EmailProvider.GMAIL:
            gmail_service = GmailService(db)
            emails = gmail_service.get_recent_emails(connection)
        elif connection.provider == EmailProvider.OUTLOOK:
            outlook_service = OutlookService(db)
            emails = outlook_service.get_recent_emails(connection)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported provider"
            )
        
        # Traiter chaque email
        processing_service = EmailProcessingService(db)
        processed_count = 0
        
        for email_data in emails:
            # Vérifier si l'email n'a pas déjà été traité
            existing = db.query(InterceptedEmail).filter(
                InterceptedEmail.connection_id == connection_id,
                InterceptedEmail.sender_email == email_data['sender_email'],
                InterceptedEmail.subject == email_data['subject']
            ).first()
            
            if not existing:
                processing_service.process_intercepted_email(email_data, connection_id, current_user.id)
                processed_count += 1
        
        return {"message": f"Synchronized {processed_count} new emails"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email sync failed: {str(e)}"
        )

@router.get("/intercepted", response_model=List[InterceptedEmailWithClient])
def get_intercepted_emails(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les emails interceptés"""
    query = db.query(
        InterceptedEmail,
        Client.name.label("client_name"),
        Client.company.label("client_company")
    ).outerjoin(Client).filter(
        InterceptedEmail.user_id == current_user.id
    ).order_by(InterceptedEmail.email_received_at.desc())
    
    results = query.all()
    
    emails_with_client = []
    for email, client_name, client_company in results:
        email_dict = {
            "id": email.id,
            "user_id": email.user_id,
            "connection_id": email.connection_id,
            "client_id": email.client_id,
            "sender_email": email.sender_email,
            "sender_name": email.sender_name,
            "subject": email.subject,
            "body": email.body,
            "confidence_score": email.confidence_score,
            "ai_classification": email.ai_classification,
            "ai_confidence": email.ai_confidence,
            "ai_reasoning": email.ai_reasoning,
            "processing_status": email.processing_status,
            "processed_at": email.processed_at,
            "email_received_at": email.email_received_at,
            "created_at": email.created_at,
            "client_name": client_name,
            "client_company": client_company,
            "attachments": [],
            "related_request_ids": []
        }
        
        # Parse JSON fields
        if email.attachments:
            try:
                email_dict["attachments"] = json.loads(email.attachments)
            except json.JSONDecodeError:
                email_dict["attachments"] = []
        
        if email.related_request_ids:
            try:
                email_dict["related_request_ids"] = json.loads(email.related_request_ids)
            except json.JSONDecodeError:
                email_dict["related_request_ids"] = []
        
        emails_with_client.append(email_dict)
    
    return emails_with_client

@router.post("/classify/{email_id}", response_model=EmailClassificationResponse)
def classify_email(
    email_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Classifie un email avec l'IA"""
    intercepted_email = db.query(InterceptedEmail).filter(
        InterceptedEmail.id == email_id,
        InterceptedEmail.user_id == current_user.id
    ).first()
    
    if not intercepted_email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
    
    try:
        ai_service = AIClassificationService(db)
        result = ai_service.classify_email(intercepted_email)
        
        return EmailClassificationResponse(
            email_id=email_id,
            classification=result['classification'],
            confidence=result['confidence'],
            reasoning=result['reasoning'],
            related_requests=result['related_requests']
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )

@router.post("/webhook/{provider}")
async def email_webhook(
    provider: EmailProvider,
    request: FastAPIRequest,
    db: Session = Depends(get_db)
):
    """Webhook pour recevoir les notifications d'emails"""
    try:
        body = await request.body()
        
        if provider == EmailProvider.GMAIL:
            # TODO: Implémenter le traitement des webhooks Gmail
            pass
        elif provider == EmailProvider.OUTLOOK:
            # TODO: Implémenter le traitement des webhooks Outlook
            pass
        
        return {"status": "webhook received"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )
