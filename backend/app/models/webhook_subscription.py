from sqlalchemy import Column, Integer, String, BigInteger, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database.config import Base

class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("email_connections.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False)  # 'GMAIL' or 'OUTLOOK'
    
    # Gmail specific (Pub/Sub)
    topic_name = Column(String(500), nullable=True)
    history_id = Column(BigInteger, nullable=True)
    
    # Outlook specific (Microsoft Graph)
    subscription_id = Column(String(500), nullable=True)
    resource = Column(String(500), nullable=True)
    client_state = Column(String(255), nullable=True)
    
    # Common fields
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False, default='active')
    last_notification_at = Column(DateTime(timezone=True), nullable=True)
    notification_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

