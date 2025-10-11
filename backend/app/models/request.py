from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.config import Base
import enum

class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    OVERDUE = "overdue"

class RequestType(str, enum.Enum):
    OUTGOING = "outgoing"  # Nos demandes vers les clients
    INCOMING = "incoming"  # Demandes reçues des clients

class RequestPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ReminderFrequency(str, enum.Enum):
    NEVER = "never"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING, nullable=False)
    priority = Column(Enum(RequestPriority), default=RequestPriority.MEDIUM, nullable=False)
    type = Column(Enum(RequestType), nullable=False)
    due_date = Column(DateTime(timezone=True))
    reminder_frequency = Column(Enum(ReminderFrequency), default=ReminderFrequency.NEVER)
    email_recipients = Column(Text)  # JSON string of email addresses
    attachments = Column(Text)  # JSON string of file paths
    is_priority = Column(Boolean, default=False)  # Pour affichage en haut
    
    # Confirmation tracking (pour ingoing et outgoing requests)
    confirmation_received = Column(Boolean, default=False)
    confirmation_received_at = Column(DateTime(timezone=True), nullable=True)
    confirmation_details = Column(Text, nullable=True)  # Détails de la confirmation (automatique via IA)
    
    # Foreign Keys
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    client = relationship("Client", back_populates="requests")
    user = relationship("User", back_populates="requests")
