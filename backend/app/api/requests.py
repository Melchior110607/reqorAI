from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import json
from datetime import datetime, timezone, timedelta
from app.database.config import get_db
from app.schemas.request import RequestCreate, RequestUpdate, RequestResponse, RequestWithClient
from app.models.request import Request, RequestType, RequestStatus, RequestPriority
from app.models.client import Client
from app.models.user import User
from app.api.dependencies import get_current_user
import openai
from app.database.config import settings

router = APIRouter(prefix="/requests", tags=["Requests"])

@router.post("/", response_model=RequestResponse)
def create_request(
    request_data: RequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify client belongs to user
    client = db.query(Client).filter(
        Client.id == request_data.client_id,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    # Convert email list to JSON string
    email_recipients_json = None
    if request_data.email_recipients:
        email_recipients_json = json.dumps(request_data.email_recipients)
    
    # Auto-assign email connection for outgoing requests if not provided
    email_connection_id = request_data.email_connection_id
    if request_data.type == RequestType.OUTGOING and not email_connection_id:
        from app.models.email_connection import EmailConnection
        # Get first available email connection for this user
        first_connection = db.query(EmailConnection).filter(
            EmailConnection.user_id == current_user.id
        ).first()
        if first_connection:
            email_connection_id = first_connection.id
    
    # Auto-assign due_date if not provided (default to 7 days from now)
    due_date = request_data.due_date
    if not due_date:
        from datetime import datetime, timedelta, timezone
        due_date = datetime.now(timezone.utc) + timedelta(days=7)
    
    db_request = Request(
        **request_data.dict(exclude={"email_recipients", "email_connection_id", "due_date"}),
        user_id=current_user.id,
        email_recipients=email_recipients_json,
        email_connection_id=email_connection_id,
        due_date=due_date
    )
    
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    # Parse email recipients for response
    response_dict = {
        "id": db_request.id,
        "title": db_request.title,
        "description": db_request.description,
        "status": db_request.status,
        "priority": db_request.priority,
        "type": db_request.type,
        "due_date": db_request.due_date,
        "reminder_frequency": db_request.reminder_frequency,
        "is_priority": db_request.is_priority,
        "client_id": db_request.client_id,
        "user_id": db_request.user_id,
        "created_at": db_request.created_at,
        "updated_at": db_request.updated_at,
        "email_recipients": [],
        "attachments": []
    }
    
    if db_request.email_recipients:
        try:
            parsed_emails = json.loads(db_request.email_recipients)
            # Ensure it's a list
            if isinstance(parsed_emails, list):
                response_dict["email_recipients"] = parsed_emails
            else:
                response_dict["email_recipients"] = []
        except json.JSONDecodeError:
            response_dict["email_recipients"] = []
    
    if db_request.attachments:
        try:
            response_dict["attachments"] = json.loads(db_request.attachments)
        except json.JSONDecodeError:
            response_dict["attachments"] = []
    
    return response_dict

@router.get("/", response_model=List[RequestWithClient])
def get_requests(
    request_type: Optional[RequestType] = Query(None),
    status: Optional[RequestStatus] = Query(None),
    priority: Optional[RequestPriority] = Query(None),
    client_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.email_connection import EmailConnection
    
    query = db.query(
        Request, 
        Client.name.label("client_name"), 
        Client.company.label("client_company"),
        EmailConnection.email_address.label("email_connection_email")
    ).join(
        Client
    ).outerjoin(
        EmailConnection, Request.email_connection_id == EmailConnection.id
    )
    query = query.filter(Request.user_id == current_user.id)
    
    if request_type:
        query = query.filter(Request.type == request_type)
    if status:
        query = query.filter(Request.status == status)
    if priority:
        query = query.filter(Request.priority == priority)
    if client_id:
        query = query.filter(Request.client_id == client_id)
    
    # Order by priority flag first, then by creation date
    query = query.order_by(Request.is_priority.desc(), Request.created_at.desc())
    
    results = query.all()
    
    # Transform results to include client info
    requests_with_client = []
    for request, client_name, client_company, email_connection_email in results:
        request_dict = {
            "id": request.id,
            "title": request.title,
            "description": request.description,
            "status": request.status,
            "priority": request.priority,
            "type": request.type,
            "due_date": request.due_date,
            "reminder_frequency": request.reminder_frequency,
            "is_priority": request.is_priority,
            "client_id": request.client_id,
            "user_id": request.user_id,
            "created_at": request.created_at,
            "updated_at": request.updated_at,
            "client_name": client_name,
            "client_company": client_company,
            "email_connection_id": request.email_connection_id,
            "email_connection_email": email_connection_email,
            "draft_response": request.draft_response,
            "draft_generated_at": request.draft_generated_at,
            "confirmation_received": request.confirmation_received,
            "confirmation_received_at": request.confirmation_received_at,
            "confirmation_details": request.confirmation_details,
            # Reminder fields (for outgoing requests)
            "reminder_enabled": request.reminder_enabled,
            "reminder_message": request.reminder_message,
            "last_reminder_sent_at": request.last_reminder_sent_at,
            "reminder_count": request.reminder_count,
            # Follow-up fields (for incoming requests)
            "is_follow_up": request.is_follow_up,
            "parent_request_id": request.parent_request_id,
            "follow_up_type": request.follow_up_type,
            "follow_up_count": request.follow_up_count,
            "latest_follow_up_message": request.latest_follow_up_message,
            "latest_follow_up_at": request.latest_follow_up_at,
            "email_recipients": [],
            "attachments": []
        }
        
        # Parse email recipients JSON
        if request.email_recipients:
            try:
                parsed_emails = json.loads(request.email_recipients)
                # Ensure it's a list
                if isinstance(parsed_emails, list):
                    request_dict["email_recipients"] = parsed_emails
                else:
                    request_dict["email_recipients"] = []
            except json.JSONDecodeError:
                request_dict["email_recipients"] = []
        
        # Parse attachments JSON
        if request.attachments:
            try:
                request_dict["attachments"] = json.loads(request.attachments)
            except json.JSONDecodeError:
                request_dict["attachments"] = []
        
        requests_with_client.append(request_dict)
    
    return requests_with_client

@router.get("/{request_id}", response_model=RequestWithClient)
def get_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.email_connection import EmailConnection
    
    result = db.query(
        Request, 
        Client.name.label("client_name"), 
        Client.company.label("client_company"),
        EmailConnection.email_address.label("email_connection_email")
    ).join(
        Client
    ).outerjoin(
        EmailConnection, Request.email_connection_id == EmailConnection.id
    ).filter(
        Request.id == request_id,
        Request.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    request, client_name, client_company, email_connection_email = result
    
    # Parse JSON fields
    request_dict = {
        "id": request.id,
        "title": request.title,
        "description": request.description,
        "status": request.status,
        "priority": request.priority,
        "type": request.type,
        "due_date": request.due_date,
        "reminder_frequency": request.reminder_frequency,
        "is_priority": request.is_priority,
        "client_id": request.client_id,
        "user_id": request.user_id,
        "created_at": request.created_at,
        "updated_at": request.updated_at,
        "client_name": client_name,
        "client_company": client_company,
        "email_connection_id": request.email_connection_id,
        "email_connection_email": email_connection_email,
        "draft_response": request.draft_response,
        "draft_generated_at": request.draft_generated_at,
        "confirmation_received": request.confirmation_received,
        "confirmation_received_at": request.confirmation_received_at,
        "confirmation_details": request.confirmation_details,
        # Reminder fields (for outgoing requests)
        "reminder_enabled": request.reminder_enabled,
        "reminder_message": request.reminder_message,
        "last_reminder_sent_at": request.last_reminder_sent_at,
        "reminder_count": request.reminder_count,
        # Follow-up fields (for incoming requests)
        "is_follow_up": request.is_follow_up,
        "parent_request_id": request.parent_request_id,
        "follow_up_type": request.follow_up_type,
        "follow_up_count": request.follow_up_count,
        "latest_follow_up_message": request.latest_follow_up_message,
        "latest_follow_up_at": request.latest_follow_up_at,
        "email_recipients": [],
        "attachments": []
    }
    
    if request.email_recipients:
        try:
            parsed_emails = json.loads(request.email_recipients)
            # Ensure it's a list
            if isinstance(parsed_emails, list):
                request_dict["email_recipients"] = parsed_emails
            else:
                request_dict["email_recipients"] = []
        except json.JSONDecodeError:
            request_dict["email_recipients"] = []
    
    if request.attachments:
        try:
            request_dict["attachments"] = json.loads(request.attachments)
        except json.JSONDecodeError:
            request_dict["attachments"] = []
    
    return request_dict

@router.put("/{request_id}", response_model=RequestResponse)
def update_request(
    request_id: int,
    request_update: RequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    request = db.query(Request).filter(
        Request.id == request_id,
        Request.user_id == current_user.id
    ).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    update_data = request_update.dict(exclude_unset=True)
    
    # Handle email recipients
    if "email_recipients" in update_data and update_data["email_recipients"]:
        update_data["email_recipients"] = json.dumps(update_data["email_recipients"])
    
    for field, value in update_data.items():
        setattr(request, field, value)
    
    db.commit()
    db.refresh(request)
    
    # Format response like in create_request
    response_dict = {
        "id": request.id,
        "title": request.title,
        "description": request.description,
        "status": request.status,
        "priority": request.priority,
        "type": request.type,
        "due_date": request.due_date,
        "reminder_frequency": request.reminder_frequency,
        "is_priority": request.is_priority,
        "client_id": request.client_id,
        "user_id": request.user_id,
        "created_at": request.created_at,
        "updated_at": request.updated_at,
        "email_recipients": [],
        "attachments": []
    }
    
    if request.email_recipients:
        try:
            parsed_emails = json.loads(request.email_recipients)
            # Ensure it's a list
            if isinstance(parsed_emails, list):
                response_dict["email_recipients"] = parsed_emails
            else:
                response_dict["email_recipients"] = []
        except json.JSONDecodeError:
            response_dict["email_recipients"] = []
    
    if request.attachments:
        try:
            response_dict["attachments"] = json.loads(request.attachments)
        except json.JSONDecodeError:
            response_dict["attachments"] = []
    
    return response_dict

@router.delete("/{request_id}")
def delete_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    request = db.query(Request).filter(
        Request.id == request_id,
        Request.user_id == current_user.id
    ).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    db.delete(request)
    db.commit()
    return {"message": "Request deleted successfully"}

@router.get("/client/{client_id}", response_model=List[RequestResponse])
def get_requests_by_client(
    client_id: int,
    request_type: Optional[RequestType] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify client belongs to user
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    query = db.query(Request).filter(Request.client_id == client_id)
    
    if request_type:
        query = query.filter(Request.type == request_type)
    
    query = query.order_by(Request.is_priority.desc(), Request.created_at.desc())
    requests = query.all()
    
    return requests

@router.post("/{request_id}/regenerate-draft")
def regenerate_draft_response(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate draft response for an incoming request"""
    from app.services.ai_agent_service import AIAgentService
    
    agent_service = AIAgentService(db)
    result = agent_service.regenerate_draft_response(request_id, current_user.id)
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('message', 'Failed to regenerate draft')
        )
    
    return result

@router.post("/{request_id}/send-draft")
def send_draft_response(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send the draft response email"""
    from app.models.email_connection import EmailConnection
    from app.services.gmail_service import GmailService
    from app.services.outlook_service import OutlookService
    
    # Get request
    request = db.query(Request).filter(
        Request.id == request_id,
        Request.user_id == current_user.id
    ).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    if not request.draft_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No draft response available"
        )
    
    # Get email connection
    if not request.email_connection_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email connection associated with this request"
        )
    
    connection = db.query(EmailConnection).filter(
        EmailConnection.id == request.email_connection_id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email connection not found"
        )
    
    # Get client for recipient
    client = db.query(Client).filter(
        Client.id == request.client_id
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found"
        )
    
    try:
        # Send email based on provider
        if connection.provider.value == "gmail":
            gmail_service = GmailService(db)
            result = gmail_service.send_email(
                connection=connection,
                to_email=client.email,
                subject=f"Re: {request.title}",
                body=request.draft_response
            )
        elif connection.provider.value == "outlook":
            outlook_service = OutlookService(db)
            result = outlook_service.send_email(
                connection=connection,
                to_email=client.email,
                subject=f"Re: {request.title}",
                body=request.draft_response
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {connection.provider}"
            )
        
        # Update request status
        request.status = RequestStatus.COMPLETED
        db.commit()
        
        return {
            "success": True,
            "message": "Email sent successfully",
            "provider": connection.provider.value,
            "to": client.email
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/{request_id}/configure-reminder")
def configure_reminder(
    request_id: int,
    reminder_enabled: bool,
    reminder_frequency: str,
    reminder_message: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Configure automatic reminder for an outgoing request"""
    from app.models.request import ReminderFrequency
    
    # Get request
    request = db.query(Request).filter(
        Request.id == request_id,
        Request.user_id == current_user.id
    ).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Only for outgoing requests
    if request.type != RequestType.OUTGOING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reminders are only available for outgoing requests"
        )
    
    # Validate frequency
    try:
        freq = ReminderFrequency(reminder_frequency)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid reminder frequency. Must be one of: {[f.value for f in ReminderFrequency]}"
        )
    
    # Update request
    request.reminder_enabled = reminder_enabled
    request.reminder_frequency = freq
    request.reminder_message = reminder_message
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Reminder {'enabled' if reminder_enabled else 'disabled'}",
        "reminder_frequency": reminder_frequency,
        "has_custom_message": bool(reminder_message)
    }


@router.post("/{request_id}/send-reminder-now")
def send_reminder_now(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually send a reminder for an outgoing request and digga"""
    from app.services.reminder_service import ReminderService
    
    # Get request
    request = db.query(Request).filter(
        Request.id == request_id,
        Request.user_id == current_user.id
    ).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Only for outgoing requests
    if request.type != RequestType.OUTGOING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reminders are only available for outgoing requests"
        )
    
    # Send reminder
    reminder_service = ReminderService(db)
    result = reminder_service.send_reminder(request)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Failed to send reminder")
        )
    
    return result


@router.get("/{request_id}/follow-ups")
def get_request_followups(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all follow-up requests for a given request"""
    # Get parent request
    parent_request = db.query(Request).filter(
        Request.id == request_id,
        Request.user_id == current_user.id
    ).first()
    
    if not parent_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Get follow-ups
    follow_ups = db.query(Request).filter(
        Request.parent_request_id == request_id,
        Request.is_follow_up == True
    ).order_by(Request.created_at.desc()).all()
    
    return {
        "parent_request_id": request_id,
        "follow_up_count": len(follow_ups),
        "follow_ups": [
            {
                "id": req.id,
                "title": req.title,
                "follow_up_type": req.follow_up_type,
                "created_at": req.created_at,
                "status": req.status.value,
                "priority": req.priority.value
            } for req in follow_ups
        ]
    }


@router.get("/{request_id}/conversation-thread")
def get_conversation_thread(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full conversation thread (parent + all follow-ups)"""
    # Get request (could be parent or follow-up)
    request = db.query(Request).filter(
        Request.id == request_id,
        Request.user_id == current_user.id
    ).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Find root parent
    root_request = request
    if request.is_follow_up and request.parent_request_id:
        root_request = db.query(Request).filter(Request.id == request.parent_request_id).first()
        if not root_request:
            root_request = request  # Fallback
    
    # Get all follow-ups
    follow_ups = db.query(Request).filter(
        Request.parent_request_id == root_request.id,
        Request.is_follow_up == True
    ).order_by(Request.created_at.asc()).all()
    
    # Build thread
    thread = [
        {
            "id": root_request.id,
            "title": root_request.title,
            "description": root_request.description,
            "draft_response": root_request.draft_response,
            "created_at": root_request.created_at,
            "status": root_request.status.value,
            "is_root": True,
            "follow_up_type": None
        }
    ]
    
    for follow_up in follow_ups:
        thread.append({
            "id": follow_up.id,
            "title": follow_up.title,
            "description": follow_up.description,
            "draft_response": follow_up.draft_response,
            "created_at": follow_up.created_at,
            "status": follow_up.status.value,
            "is_root": False,
            "follow_up_type": follow_up.follow_up_type
        })
    
    return {
        "root_request_id": root_request.id,
        "thread_length": len(thread),
        "total_follow_ups": len(follow_ups),
        "conversation": thread
    }


@router.post("/{request_id}/mark-confirmation")
def mark_confirmation(
    request_id: int,
    confirmation_details: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually mark an outgoing request as confirmed"""
    request = db.query(Request).filter(
        Request.id == request_id,
        Request.user_id == current_user.id
    ).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Only for outgoing requests
    if request.type != RequestType.OUTGOING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only outgoing requests can be marked as confirmed"
        )
    
    # Update confirmation fields
    request.confirmation_received = True
    request.confirmation_received_at = datetime.now(timezone.utc)
    if confirmation_details:
        request.confirmation_details = confirmation_details
    
    db.commit()
    
    return {
        "success": True,
        "message": "Request marked as confirmed",
        "confirmation_received_at": request.confirmation_received_at
    }


@router.delete("/{request_id}/unmark-confirmation")
def unmark_confirmation(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove confirmation status from an outgoing request"""
    request = db.query(Request).filter(
        Request.id == request_id,
        Request.user_id == current_user.id
    ).first()
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Clear confirmation fields
    request.confirmation_received = False
    request.confirmation_received_at = None
    request.confirmation_details = None
    
    db.commit()
    
    return {
        "success": True,
        "message": "Confirmation status removed"
    }

@router.post("/ai-chat")
def ai_chat_request(
    chat_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Conversational AI endpoint for creating requests
    
    Body: {
        "message": "user message",
        "conversation_history": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ],
        "extracted_data": {
            "title": "...",
            "description": "...",
            "client_name": "...",
            ...
        }
    }
    """
    user_message = chat_data.get("message", "")
    conversation_history = chat_data.get("conversation_history", [])
    extracted_data = chat_data.get("extracted_data", {})
    
    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message is required"
        )
    
    # Get all clients for the user (for matching)
    clients = db.query(Client).filter(Client.user_id == current_user.id).all()
    clients_list = [{"id": c.id, "name": c.name, "company": c.company, "email": c.email} for c in clients]
    
    # Get email connections for the user
    from app.models.email_connection import EmailConnection
    email_connections = db.query(EmailConnection).filter(EmailConnection.user_id == current_user.id).all()
    email_connections_list = [{"id": ec.id, "email": ec.email_address, "provider": ec.provider.value} for ec in email_connections]
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=settings.openai_api_key)
    
    # Build system prompt
    system_prompt = f"""You are Reqor, a conversational AI assistant that helps create requests.

CRITICAL RULES:
1. YOU create the title and description yourself from the user's brief description - DON'T ASK FOR THEM
2. NEVER AS QUESTIONS IF HE MENTIONS EVERYTHING.
3. ONLY ask for: client (if not mentioned), due_date (if not mentioned), priority (if not clear), type (if not clear), email_connection_id (for outgoing requests only), reminder settings (for outgoing requests)
4. Keep questions SHORT and ONE at a time
5. When you have ALL required info, return ONLY the JSON (no extra text)

INFORMATION NEEDED:
- **title**: YOU create this (short, clear) - DON'T ASK
- **description**: YOU create this (detailed) - DON'T ASK  
- **type**: "incoming" (from client) or "outgoing" (to client) - ask if unclear
- **priority**: "low", "medium", "high", or "urgent" - ask if not obvious
- **client_id**: Match from list below - ask if not mentioned
- **due_date**: ISO format YYYY-MM-DD - ask if not mentioned
- **email_connection_id**: For outgoing requests, which email to use - ask user to choose
- **reminder_enabled**: For OUTGOING requests only, ask "Would you like automatic reminders?"
- **reminder_frequency**: If reminder enabled, ask frequency: "never", "daily", "weekly", "biweekly", "monthly"

AVAILABLE CLIENTS:
{json.dumps(clients_list, indent=2)}

AVAILABLE EMAIL ACCOUNTS (for outgoing requests):
{json.dumps(email_connections_list, indent=2)}

CURRENT DATE: {datetime.now().strftime("%Y-%m-%d %A")}

ALREADY EXTRACTED DATA:
{json.dumps(extracted_data, indent=2)}

WHEN READY, return ONLY this JSON (ABSOLUTELY NO OTHER TEXT, NO EXPLANATIONS, NO GREETINGS):
{{
    "action": "create_request",
    "ready": true,
    "data": {{
        "title": "YOUR_CREATED_TITLE",
        "description": "YOUR_CREATED_DESCRIPTION",
        "type": "incoming/outgoing",
        "priority": "low/medium/high/urgent",
        "client_id": 123,
        "due_date": "YYYY-MM-DD",
        "email_connection_id": 1,
        "reminder_enabled": true/false,
        "reminder_frequency": "never/daily/weekly/biweekly/monthly"
    }}
}}

CRITICAL: When you have all info, respond with ONLY the JSON above. NO "Here is your request", NO "Perfect", NOTHING ELSE. Just the raw JSON.

NOTES:
- email_connection_id is ONLY for outgoing requests. For incoming, omit it or set to null.
- reminder_enabled and reminder_frequency are ONLY for outgoing requests. For incoming, omit them.
- If user doesn't want reminders, set reminder_enabled to false and reminder_frequency to "never".
"""
    
    # Build conversation with history
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})
    
    # Call OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
        max_tokens=1000
    )
    
    assistant_message = response.choices[0].message.content.strip()
    
    # Try to extract JSON from response (in case AI added text around it)
    import re
    json_match = re.search(r'\{[\s\S]*"action"\s*:\s*"create_request"[\s\S]*\}', assistant_message)
    
    if json_match:
        json_str = json_match.group(0)
        try:
            response_json = json.loads(json_str)
            if response_json.get("action") == "create_request" and response_json.get("ready"):
                # Extract data and create request
                data = response_json.get("data", {})
                
                # Parse reminder frequency
                from app.models.request import ReminderFrequency
                reminder_freq = data.get("reminder_frequency", "never")
                try:
                    reminder_frequency = ReminderFrequency(reminder_freq)
                except ValueError:
                    reminder_frequency = ReminderFrequency.NEVER
                
                # For INCOMING requests, auto-assign first email connection if not specified
                email_connection_id_to_use = data.get("email_connection_id")
                if not email_connection_id_to_use and data.get("type") == "incoming":
                    # Get first available email connection for this user
                    if email_connections and len(email_connections) > 0:
                        email_connection_id_to_use = email_connections[0].id
                        print(f"✅ Auto-assigned email connection {email_connections[0].email_address} for incoming request")
                
                # Create the request
                request_create = Request(
                    title=data.get("title"),
                    description=data.get("description"),
                    type=RequestType(data.get("type")),
                    priority=RequestPriority(data.get("priority", "medium")),
                    status=RequestStatus.PENDING,
                    client_id=data.get("client_id"),
                    user_id=current_user.id,
                    due_date=datetime.fromisoformat(data.get("due_date")) if data.get("due_date") else None,
                    email_connection_id=email_connection_id_to_use,
                    reminder_enabled=data.get("reminder_enabled", False),
                    reminder_frequency=reminder_frequency
                )
                
                db.add(request_create)
                db.commit()
                db.refresh(request_create)
                
                # For INCOMING requests, auto-generate draft response using RAG
                if request_create.type == RequestType.INCOMING:
                    try:
                        from app.services.ai_agent_service import AIAgentService
                        
                        # Get client for draft generation
                        client_obj = db.query(Client).filter(Client.id == request_create.client_id).first()
                        
                        if client_obj:
                            # Create pseudo-email for draft generation
                            class PseudoEmail:
                                def __init__(self, request):
                                    self.subject = request.title
                                    self.body = request.description
                                    self.anonymized_body = request.description  # No PII in chat-created requests
                            
                            agent_service = AIAgentService(db)
                            draft = agent_service._generate_draft_response(
                                email=PseudoEmail(request_create),
                                client=client_obj,
                                user_id=current_user.id
                            )
                            
                            request_create.draft_response = draft
                            request_create.draft_generated_at = datetime.now(timezone.utc)
                            db.commit()
                            
                            print(f"✅ Auto-generated draft response for incoming request {request_create.id}")
                    except Exception as e:
                        print(f"⚠️ Failed to auto-generate draft: {str(e)}")
                        # Continue anyway - request is created, just without draft
                
                return {
                    "type": "request_created",
                    "message": f"✅ Perfect! I've created the request '{request_create.title}' (ID: {request_create.id})",
                    "request_id": request_create.id,
                    "ready": True,
                    "has_draft": request_create.draft_response is not None if request_create.type == RequestType.INCOMING else False
                }
        except json.JSONDecodeError:
            # Failed to parse JSON
            print(f"⚠️ Failed to parse JSON from AI response: {json_str}")
            pass
    
    # If we reach here, it's a normal conversational response (not a JSON)
    
    # Update extracted data by parsing assistant's understanding
    # (This is optional - you could also ask the AI to return structured data)
    
    return {
        "type": "conversation",
        "message": assistant_message,
        "ready": False
    }
