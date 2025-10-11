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
from app.models.sync_log import SyncLog
from app.api.dependencies import get_current_user
from app.services.gmail_service import GmailService
from app.services.outlook_service import OutlookService
from app.services.email_service import EmailProcessingService
from app.services.ai_service import AIClassificationService
from app.services.gmail_webhook_service import GmailWebhookService
from app.services.outlook_webhook_service import OutlookWebhookService

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
            
            # ✅ AUTO-SETUP WEBHOOK for Gmail
            try:
                gmail_webhook = GmailWebhookService(db)
                webhook_result = gmail_webhook.setup_watch(connection)
                print(f"✅ Gmail webhook auto-setup: {webhook_result}")
            except Exception as webhook_error:
                print(f"⚠️ Gmail webhook auto-setup failed (non-critical): {str(webhook_error)}")
                # Don't fail the whole OAuth if webhook setup fails
            
        elif provider == EmailProvider.OUTLOOK:
            outlook_service = OutlookService(db)
            connection = outlook_service.handle_oauth_callback(code, state)
            
            # ✅ AUTO-SETUP WEBHOOK for Outlook
            try:
                outlook_webhook = OutlookWebhookService(db)
                webhook_result = outlook_webhook.create_subscription(connection)
                print(f"✅ Outlook webhook auto-setup: {webhook_result}")
            except Exception as webhook_error:
                print(f"⚠️ Outlook webhook auto-setup failed (non-critical): {str(webhook_error)}")
                # Don't fail the whole OAuth if webhook setup fails
            
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
    
    # Stop webhook before deleting
    try:
        if connection.provider == EmailProvider.GMAIL:
            gmail_webhook = GmailWebhookService(db)
            gmail_webhook.stop_watch(connection)
        elif connection.provider == EmailProvider.OUTLOOK:
            outlook_webhook = OutlookWebhookService(db)
            outlook_webhook.delete_subscription(connection)
    except Exception as e:
        print(f"⚠️ Warning: Failed to stop webhook: {str(e)}")
    
    db.delete(connection)
    db.commit()
    
    return {"message": "Email connection deleted successfully"}

@router.post("/webhook/setup/{connection_id}")
def setup_webhook(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup webhook for an email connection"""
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
            gmail_webhook = GmailWebhookService(db)
            result = gmail_webhook.setup_watch(connection)
            return {
                "message": "Gmail webhook setup successful",
                "provider": "gmail",
                **result
            }
        
        elif connection.provider == EmailProvider.OUTLOOK:
            outlook_webhook = OutlookWebhookService(db)
            result = outlook_webhook.create_subscription(connection)
            return {
                "message": "Outlook webhook setup successful",
                "provider": "outlook",
                **result
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported provider"
            )
            
    except Exception as e:
        print(f"❌ Webhook setup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup webhook: {str(e)}"
        )

@router.post("/sync/{provider_name}")
def sync_emails_by_provider_name(
    provider_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Synchronise manuellement les emails - DEBUG"""
    # Trouver la connexion de l'utilisateur pour ce provider
    provider = EmailProvider.GMAIL if provider_name == 'gmail' else EmailProvider.OUTLOOK
    connection = db.query(EmailConnection).filter(
        EmailConnection.user_id == current_user.id,
        EmailConnection.provider == provider
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pas de connexion {provider_name} trouvée. Connectez-vous d'abord avec OAuth."
        )
    
    try:
        from datetime import datetime, timezone
        
        # Récupérer uniquement les emails depuis la dernière sync
        since_timestamp = connection.last_sync if connection.last_sync else None
        
        if connection.provider == EmailProvider.GMAIL:
            gmail_service = GmailService(db)
            emails = gmail_service.get_recent_emails(connection, max_results=50, since_timestamp=since_timestamp)
        elif connection.provider == EmailProvider.OUTLOOK:
            outlook_service = OutlookService(db)
            emails = outlook_service.get_recent_emails(connection, max_results=50, since_timestamp=since_timestamp)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported provider"
            )
        
        # Traiter chaque email avec anti-doublon intégré
        processing_service = EmailProcessingService(db)
        processed_count = 0
        duplicate_count = 0
        
        for email_data in emails:
            result = processing_service.process_intercepted_email(email_data, connection.id, current_user.id)
            if result:
                processed_count += 1
            else:
                duplicate_count += 1
        
        # Mettre à jour last_sync
        connection.last_sync = datetime.now(timezone.utc)
        db.commit()
        
        message = f"✅ {processed_count} nouveaux emails"
        if duplicate_count > 0:
            message += f" ({duplicate_count} doublons évités)"
        
        return {"message": message, "count": processed_count, "duplicates": duplicate_count}
        
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
    """Récupère TOUS les emails interceptés avec infos client"""
    
    # Récupérer tous les emails de l'utilisateur, triés par date
    emails = db.query(InterceptedEmail).filter(
        InterceptedEmail.user_id == current_user.id
    ).order_by(InterceptedEmail.email_received_at.desc()).all()
    
    emails_list = []
    for email in emails:
        # Charger les infos du client si client_id existe
        client_name = None
        client_company = None
        if email.client_id:
            client = db.query(Client).filter(Client.id == email.client_id).first()
            if client:
                client_name = client.name
                client_company = client.company
        
        # Parser related_request_ids si c'est un JSON string
        related_requests = []
        if email.related_request_ids:
            try:
                related_requests = json.loads(email.related_request_ids) if isinstance(email.related_request_ids, str) else email.related_request_ids
            except:
                related_requests = []
        
        # Charger la règle de matching si elle existe
        rule_type = None
        rule_pattern = None
        if email.matched_rule_id:
            from app.models.client_email_rule import ClientEmailRule
            rule = db.query(ClientEmailRule).filter(ClientEmailRule.id == email.matched_rule_id).first()
            if rule:
                rule_type = rule.rule_type.value
                rule_pattern = rule.pattern
        
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
            "matched_rule_id": email.matched_rule_id,
            "rule_type": rule_type,
            "rule_pattern": rule_pattern,
            "ai_classification": email.ai_classification.value if email.ai_classification else None,
            "ai_confidence": email.ai_confidence,
            "ai_reasoning": email.ai_reasoning,
            "processing_status": email.processing_status.value if email.processing_status else None,
            "processed_at": email.processed_at,
            "email_received_at": email.email_received_at,
            "created_at": email.created_at,
            "client_name": client_name,
            "client_company": client_company,
            "attachments": [],
            "related_request_ids": related_requests
        }
        
        emails_list.append(email_dict)
    
    return emails_list

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
        print(f"🤖 Starting classification for email {email_id}")
        ai_service = AIClassificationService(db)
        print(f"🤖 AIClassificationService initialized")
        result = ai_service.classify_email(intercepted_email)
        print(f"🤖 Classification result: {result.get('classification')}")
        
        # Convertir la string en enum
        from app.models.intercepted_email import EmailClassification as EmailClassificationEnum
        classification_enum = EmailClassificationEnum(result['classification'])
        
        return EmailClassificationResponse(
            email_id=email_id,
            classification=classification_enum,
            confidence=result['confidence'],
            reasoning=result['reasoning'],
            related_requests=result['related_requests']
        )
        
    except Exception as e:
        import traceback
        print(f"❌ Classification error for email {email_id}:")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {str(e)}"
        )

@router.post("/classify-all")
def classify_all_pending_emails(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Classifie TOUS les emails PENDING de l'utilisateur - SEQUENTIELLEMENT
    Les appels OpenAI sont faits un par un pour éviter les erreurs
    """
    from app.models.intercepted_email import ProcessingStatus
    
    try:
        # Récupérer tous les emails PENDING avec client_id non null
        pending_emails = db.query(InterceptedEmail).filter(
            InterceptedEmail.user_id == current_user.id,
            InterceptedEmail.processing_status == ProcessingStatus.PENDING,
            InterceptedEmail.client_id.isnot(None)  # Seulement les emails matchés
        ).all()
        
        if not pending_emails:
            return {
                "message": "No pending emails to classify",
                "total": 0,
                "classified": 0,
                "failed": 0,
                "skipped": 0
            }
        
        ai_service = AIClassificationService(db)
        classified_count = 0
        failed_count = 0
        skipped_count = 0
        results = []
        
        # IMPORTANT: Traitement SEQUENTIEL (un email à la fois)
        for email in pending_emails:
            try:
                print(f"🤖 Classifying email {email.id} from {email.sender_email}...")
                result = ai_service.classify_email(email)
                classified_count += 1
                results.append({
                    "email_id": email.id,
                    "status": "classified",
                    "classification": result['classification'],
                    "confidence": result['confidence']
                })
                print(f"✅ Email {email.id} classified as {result['classification']}")
                
            except Exception as e:
                failed_count += 1
                error_msg = str(e)
                print(f"❌ Failed to classify email {email.id}: {error_msg}")
                results.append({
                    "email_id": email.id,
                    "status": "failed",
                    "error": error_msg[:200]  # Limiter la taille de l'erreur
                })
                # Continuer avec le prochain email même en cas d'erreur
                continue
        
        return {
            "message": f"Classification completed: {classified_count} classified, {failed_count} failed",
            "total": len(pending_emails),
            "classified": classified_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch classification failed: {str(e)}"
        )

@router.post("/match-clients")
def match_clients_to_emails(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Re-applique l'algorithme de matching sur TOUS les emails existants
    Pour tester l'algorithme de reconnaissance client
    """
    try:
        from app.services.email_service import EmailMatchingService
        
        matching_service = EmailMatchingService(db)
        
        # Récupérer tous les emails de l'utilisateur
        emails = db.query(InterceptedEmail).filter(
            InterceptedEmail.user_id == current_user.id
        ).all()
        
        matched_count = 0
        ignored_count = 0
        results = []
        
        for email in emails:
            # Appliquer l'algorithme de matching
            client, confidence, rule = matching_service.find_matching_client(
                email.sender_email, 
                current_user.id
            )
            
            # Mettre à jour l'email avec les résultats
            email.client_id = client.id if client else None
            email.confidence_score = confidence
            email.matched_rule_id = rule.id if rule else None
            
            if client:
                matched_count += 1
                results.append({
                    "email_id": email.id,
                    "sender_email": email.sender_email,
                    "subject": email.subject,
                    "matched": True,
                    "client_id": client.id,
                    "client_name": client.name,
                    "client_company": client.company,
                    "confidence": round(confidence, 2),
                    "rule_type": rule.rule_type.value if rule else "auto",
                    "rule_pattern": rule.pattern if rule else "automatic matching"
                })
            else:
                ignored_count += 1
                results.append({
                    "email_id": email.id,
                    "sender_email": email.sender_email,
                    "subject": email.subject,
                    "matched": False,
                    "client_id": None,
                    "client_name": None,
                    "client_company": None,
                    "confidence": 0.0,
                    "rule_type": None,
                    "rule_pattern": None
                })
        
        db.commit()
        
        return {
            "total_emails": len(emails),
            "matched_count": matched_count,
            "ignored_count": ignored_count,
            "results": results
        }
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Client matching failed: {str(e)}"
        )

# @router.post("/webhook/{provider}")
# async def email_webhook(
#     provider: EmailProvider,
#     request: FastAPIRequest,
#     db: Session = Depends(get_db)
# ):
#     """Webhook pour recevoir les notifications d'emails"""
#     try:
#         body = await request.body()
        
#         if provider == EmailProvider.GMAIL:
#             # TODO: Implémenter le traitement des webhooks Gmail
#             pass
#         elif provider == EmailProvider.OUTLOOK:
#             # TODO: Implémenter le traitement des webhooks Outlook
#             pass
        
#         return {"status": "webhook received"}
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Webhook processing failed: {str(e)}"
#         )

@router.get("/sync-logs")
def get_sync_logs(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Récupère les logs de synchronisation automatique"""
    logs = db.query(SyncLog).order_by(SyncLog.created_at.desc()).limit(limit).all()
    
    return [{
        "id": log.id,
        "sync_type": log.sync_type,
        "total_synced": log.total_synced,
        "total_duplicates": log.total_duplicates,
        "connections_processed": log.connections_processed,
        "details": log.details,
        "error": log.error,
        "created_at": log.created_at
    } for log in logs]
