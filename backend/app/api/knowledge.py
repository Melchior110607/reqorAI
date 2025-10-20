"""
Knowledge Base API - Upload and manage documents for RAG
"""
import os
import json
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import PyPDF2
import docx

from app.database.config import get_db, settings
from app.models.user import User
from app.models.knowledge_base import KnowledgeDocument
from app.api.dependencies import get_current_user
from app.services.rag_service import RAGService


router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

# Ensure uploads directory exists
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting PDF text: {str(e)}")
    return text


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    text = ""
    try:
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        print(f"Error extracting DOCX text: {str(e)}")
    return text


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading TXT file: {str(e)}")
        return ""


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload document for RAG knowledge base with intelligent chunking"""
    
    # Check file type
    allowed_extensions = ['.pdf', '.docx', '.txt']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Create user-specific directory
    user_upload_dir = os.path.join(UPLOAD_DIR, f"user_{current_user.id}")
    os.makedirs(user_upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(user_upload_dir, file.filename)
    
    try:
        contents = await file.read()
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        print(f"📄 Saved file: {file_path}")
        
        # Use improved RAG service with chunking
        rag_service = RAGService(db)
        document = rag_service.add_document(current_user.id, file_path, file.filename)
        
        return {
            "success": True,
            "document_id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "chunk_count": document.chunk_count,
            "status": document.status,
            "text_length": len(document.content_text) if document.content_text else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


@router.get("/documents")
def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's knowledge documents with chunking info"""
    documents = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.user_id == current_user.id
    ).order_by(KnowledgeDocument.upload_date.desc()).all()
    
    return [{
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "upload_date": doc.upload_date,
        "text_length": len(doc.content_text) if doc.content_text else 0,
        "chunk_count": doc.chunk_count,
        "status": doc.status
    } for doc in documents]


@router.delete("/documents/{doc_id}")
def delete_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete knowledge document"""
    document = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.user_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from disk
    if os.path.exists(document.file_path):
        try:
            os.remove(document.file_path)
            print(f"🗑️ Deleted file: {document.file_path}")
        except Exception as e:
            print(f"⚠️ Could not delete file: {str(e)}")
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

