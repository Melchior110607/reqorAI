from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.config import Base
import enum

class RuleType(str, enum.Enum):
    DOMAIN = "domain"          # @amazon.com
    CONTAINS = "contains"      # amazon dans l'email
    EXACT = "exact"           # email exact
    SUBDOMAIN = "subdomain"   # *.amazon.com

class ClientEmailRule(Base):
    __tablename__ = "client_email_rules"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    rule_type = Column(Enum(RuleType), nullable=False)
    pattern = Column(String, nullable=False)  # Le pattern à matcher
    confidence_score = Column(Float, default=1.0)  # Score de confiance (0-1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    client = relationship("Client", back_populates="email_rules")
