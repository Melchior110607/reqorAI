"""
Model for storing document chunks with embeddings
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.config import Base


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order of chunks in document
    chunk_text = Column(Text, nullable=False)  # The actual text chunk
    embedding_vector = Column(Text, nullable=False)  # JSON serialized embedding
    token_count = Column(Integer, nullable=True)  # Approximate token count
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    document = relationship("KnowledgeDocument", back_populates="chunks")

