from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database.config import Base

class SyncLog(Base):
    __tablename__ = "sync_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    sync_type = Column(String, nullable=False)  # "auto" ou "manual"
    total_synced = Column(Integer, default=0)
    total_duplicates = Column(Integer, default=0)
    connections_processed = Column(Integer, default=0)
    details = Column(JSON)  # Détails par connexion
    error = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

