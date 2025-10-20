from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.config import Base

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Local storage path
    content_text = Column(Text)  # Full extracted text
    content_preview = Column(Text, nullable=True)  # First 500 chars preview
    file_type = Column(String)  # pdf, docx, txt, etc.
    file_size = Column(Integer)
    chunk_count = Column(Integer, default=0)  # Number of chunks created
    status = Column(String, default="processing")  # processing, ready, failed
    upload_date = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    user = relationship("User")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")

