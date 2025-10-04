from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class ClientBase(BaseModel):
    name: str
    email: EmailStr
    company: str
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class ClientResponse(ClientBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
