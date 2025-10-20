from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from app.models.email_connection import EmailProvider, ConnectionStatus
from app.models.client_email_rule import RuleType
from app.models.intercepted_email import EmailClassification, ProcessingStatus

# Email Connection Schemas
class EmailConnectionBase(BaseModel):
    provider: EmailProvider
    email_address: EmailStr

class EmailConnectionCreate(EmailConnectionBase):
    pass

class EmailConnectionResponse(EmailConnectionBase):
    id: int
    user_id: int
    status: ConnectionStatus
    last_sync: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Client Email Rule Schemas
class ClientEmailRuleBase(BaseModel):
    rule_type: RuleType
    pattern: str
    confidence_score: float = 1.0
    is_active: bool = True

class ClientEmailRuleCreate(ClientEmailRuleBase):
    client_id: int

class ClientEmailRuleResponse(ClientEmailRuleBase):
    id: int
    client_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Intercepted Email Schemas
class InterceptedEmailBase(BaseModel):
    sender_email: EmailStr
    sender_name: Optional[str] = None
    subject: str
    body: str
    attachments: Optional[List[str]] = None

class InterceptedEmailCreate(InterceptedEmailBase):
    connection_id: int
    email_thread_id: Optional[str] = None
    email_received_at: datetime

class InterceptedEmailResponse(InterceptedEmailBase):
    id: int
    user_id: int
    connection_id: int
    client_id: Optional[int] = None
    confidence_score: float
    ai_classification: EmailClassification
    ai_confidence: Optional[float] = None  # Now optional (deprecated)
    ai_reasoning: Optional[str] = None
    ai_sub_classifications: Optional[str] = None  # JSON for MIXED
    related_request_ids: Optional[List[int]] = None
    processing_status: ProcessingStatus
    processed_at: Optional[datetime] = None
    email_received_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class InterceptedEmailWithClient(InterceptedEmailResponse):
    client_name: Optional[str] = None
    client_company: Optional[str] = None

# AI Classification Schemas
class EmailClassificationRequest(BaseModel):
    email_id: int

class EmailClassificationResponse(BaseModel):
    email_id: int
    classification: EmailClassification
    confidence: Optional[float] = None  # Deprecated
    reasoning: Optional[str] = None  # Deprecated
    related_requests: List[int]
    sub_classifications: Optional[List[dict]] = None  # For MIXED

# OAuth Callback Schemas
class OAuthCallbackRequest(BaseModel):
    code: str
    state: str

class AuthUrlResponse(BaseModel):
    auth_url: str
    provider: EmailProvider
