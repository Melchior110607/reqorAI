from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.request import RequestStatus, RequestType, RequestPriority, ReminderFrequency

class RequestBase(BaseModel):
    title: str
    description: str
    status: RequestStatus = RequestStatus.PENDING
    priority: RequestPriority = RequestPriority.MEDIUM
    type: RequestType
    due_date: Optional[datetime] = None
    reminder_frequency: ReminderFrequency = ReminderFrequency.NEVER
    email_recipients: Optional[List[str]] = None
    is_priority: bool = False

class RequestCreate(RequestBase):
    client_id: int
    email_connection_id: Optional[int] = None

class RequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[RequestStatus] = None
    priority: Optional[RequestPriority] = None
    due_date: Optional[datetime] = None
    reminder_frequency: Optional[ReminderFrequency] = None
    email_recipients: Optional[List[str]] = None
    is_priority: Optional[bool] = None

class RequestResponse(RequestBase):
    id: int
    client_id: int
    user_id: int
    attachments: Optional[List[str]] = None
    email_connection_id: Optional[int] = None
    draft_response: Optional[str] = None
    draft_generated_at: Optional[datetime] = None
    confirmation_received: bool = False
    confirmation_received_at: Optional[datetime] = None
    confirmation_details: Optional[str] = None
    reminder_enabled: bool = False
    reminder_message: Optional[str] = None
    last_reminder_sent_at: Optional[datetime] = None
    reminder_count: int = 0
    # Follow-up tracking (for incoming requests)
    is_follow_up: bool = False
    parent_request_id: Optional[int] = None
    follow_up_type: Optional[str] = None  # 'client_reminder' or 'dissatisfaction'
    follow_up_count: int = 0
    latest_follow_up_message: Optional[str] = None
    latest_follow_up_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RequestWithClient(RequestResponse):
    client_name: str
    client_company: str
    email_connection_email: Optional[str] = None
