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
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"

class FollowUpType(str, enum.Enum):
    CLIENT_REMINDER = "client_reminder"  # Client redemande la même chose
    DISSATISFACTION = "dissatisfaction"  # Client insatisfait de la réponse

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
    
    # AI Draft Response (pour incoming requests)
    draft_response = Column(Text, nullable=True)
    draft_generated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Auto-Reminder System (pour outgoing requests)
    reminder_enabled = Column(Boolean, default=False)
    reminder_message = Column(Text, nullable=True)  # Custom or AI-generated
    last_reminder_sent_at = Column(DateTime(timezone=True), nullable=True)
    reminder_count = Column(Integer, default=0)
    
    # Follow-up tracking (pour incoming requests)
    is_follow_up = Column(Boolean, default=False)
    parent_request_id = Column(Integer, ForeignKey("requests.id"), nullable=True)
    follow_up_type = Column(String(50), nullable=True)  # 'client_reminder' or 'dissatisfaction'
    follow_up_count = Column(Integer, default=0)
    
    # Foreign Keys
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email_connection_id = Column(Integer, ForeignKey("email_connections.id"), nullable=True)  # Connexion email associée
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    client = relationship("Client", back_populates="requests")
    user = relationship("User", back_populates="requests")
    email_connection = relationship("EmailConnection")
    parent_request = relationship("Request", remote_side=[id], foreign_keys=[parent_request_id])
    follow_ups = relationship("Request", foreign_keys=[parent_request_id], back_populates="parent_request", cascade="all, delete-orphan")
    
    @property
    def computed_status(self):
        """
        Compute actual status based on due_date
        
        If due_date is past and status is PENDING, return OVERDUE.
        Otherwise return actual status.
        """
        from datetime import datetime, timezone
        
        if self.status == RequestStatus.PENDING and self.due_date:
            if self.due_date < datetime.now(timezone.utc):
                return RequestStatus.OVERDUE
        
        return self.status
    
    @property
    def is_overdue(self) -> bool:
        """Check if request is overdue"""
        from datetime import datetime, timezone
        
        if self.status == RequestStatus.COMPLETED:
            return False
        
        if self.due_date and self.due_date < datetime.now(timezone.utc):
            return True
        
        return False
    
    @property
    def days_until_due(self) -> int:
        """Calculate days until due (negative if overdue)"""
        from datetime import datetime, timezone
        
        if not self.due_date:
            return None
        
        now = datetime.now(timezone.utc)
        delta = self.due_date - now
        return delta.days
