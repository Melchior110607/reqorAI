from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.config import Base
import enum

class EmailClassification(str, enum.Enum):
    RESPONSE_TO_REQUEST = "response_to_request"
    NEW_REQUEST = "new_request"
    CONFIRMATION = "confirmation"
    CLIENT_REMINDER = "client_reminder"
    DISSATISFACTION = "dissatisfaction"
    MIXED = "mixed"
    UNCLASSIFIED = "unclassified"

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class InterceptedEmail(Base):
    __tablename__ = "intercepted_emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("email_connections.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)  # Peut être null si pas reconnu
    
    # Email data
    message_id = Column(String, unique=True, nullable=False, index=True)  # ID unique du message (Gmail/Outlook)
    sender_email = Column(String, nullable=False)
    sender_name = Column(String)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    attachments = Column(Text)  # JSON string des pièces jointes
    email_thread_id = Column(String)  # ID du thread email
    
    # Matching data
    confidence_score = Column(Float, default=0.0)
    matched_rule_id = Column(Integer, ForeignKey("client_email_rules.id"), nullable=True)
    
    # AI Classification
    ai_classification = Column(Enum(EmailClassification), default=EmailClassification.UNCLASSIFIED)
    ai_confidence = Column(Float, default=0.0)
    ai_reasoning = Column(Text)  # Explication de l'IA
    related_request_ids = Column(Text)  # JSON array des IDs de requests liées
    
    # Processing
    processing_status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    processed_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    
    # Timestamps
    email_received_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    user = relationship("User")
    connection = relationship("EmailConnection", back_populates="intercepted_emails")
    client = relationship("Client")
    matched_rule = relationship("ClientEmailRule")
