from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.config import Base
import enum

class AuthProvider(str, enum.Enum):
    LOCAL = "local"  # Email/password classique
    GOOGLE = "google"  # OAuth Google
    MICROSOFT = "microsoft"  # OAuth Microsoft

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable pour OAuth users
    first_name = Column(String)
    last_name = Column(String)
    phone = Column(String)
    
    # OAuth fields
    auth_provider = Column(Enum(AuthProvider), default=AuthProvider.LOCAL, nullable=False)
    oauth_provider_id = Column(String, nullable=True)  # ID from Google/Microsoft
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")
    requests = relationship("Request", back_populates="user", cascade="all, delete-orphan")
    email_connections = relationship("EmailConnection", back_populates="user", cascade="all, delete-orphan")
    intercepted_emails = relationship("InterceptedEmail", back_populates="user", cascade="all, delete-orphan")
