from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
import json
from app.database.config import get_db
from app.schemas.request import RequestCreate, RequestUpdate, RequestResponse, RequestWithClient
from app.models.request import Request, RequestType, RequestStatus, RequestPriority
from app.models.client import Client
from app.models.user import User
from app.api.dependencies import get_current_user

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
    
    db_request = Request(
        **request_data.dict(exclude={"email_recipients"}),
        user_id=current_user.id,
        email_recipients=email_recipients_json
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
    query = db.query(Request, Client.name.label("client_name"), Client.company.label("client_company")).join(Client)
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
    for request, client_name, client_company in results:
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
    result = db.query(Request, Client.name.label("client_name"), Client.company.label("client_company")).join(Client).filter(
        Request.id == request_id,
        Request.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    request, client_name, client_company = result
    
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
