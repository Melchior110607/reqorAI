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
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RequestWithClient(RequestResponse):
    client_name: str
    client_company: str
