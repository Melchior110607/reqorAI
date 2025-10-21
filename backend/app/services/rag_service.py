"""
Improved RAG Service with Chunking and Better Token Management
"""
import json
import os
import re
import numpy as np
from typing import List, Dict, Any
from sqlalchemy.orm import Session
import openai
from PyPDF2 import PdfReader
from docx import Document as DocxDocument

from app.models.knowledge_base import KnowledgeDocument
from app.models.knowledge_chunk import KnowledgeChunk
from app.database.config import settings


class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Chunking parameters
        self.chunk_size = 800  # Target tokens per chunk (safe for embedding)
        self.chunk_overlap = 100  # Overlap between chunks for context continuity
        self.max_embedding_tokens = 8000  # OpenAI limit
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (1 token ≈ 4 characters for English)
        More accurate: use tiktoken library
        """
        return len(text) // 4
    
    def split_text_into_chunks(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """
        Split text into overlapping chunks of approximately chunk_size tokens
        
        Strategy:
        1. Split by paragraphs first (maintain semantic boundaries)
        2. If paragraph > chunk_size, split by sentences
        3. If sentence > chunk_size, split by words
        """
        chunks = []
        
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        current_tokens = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_tokens = self.estimate_tokens(para)
            
            # If adding this paragraph exceeds chunk_size, finalize current chunk
            if current_tokens + para_tokens > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap from end of previous chunk
                overlap_text = " ".join(current_chunk.split()[-overlap:])
                current_chunk = overlap_text + "\n\n" + para
                current_tokens = self.estimate_tokens(current_chunk)
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
                current_tokens += para_tokens
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from various file types"""
        if file_path.endswith('.pdf'):
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        elif file_path.endswith('.docx'):
            doc = DocxDocument(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        elif file_path.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
    
    def create_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            # Safety check: truncate if too long
            tokens = self.estimate_tokens(text)
            if tokens > self.max_embedding_tokens:
                print(f"⚠️ Text too long ({tokens} tokens), truncating to {self.max_embedding_tokens}")
                # Rough truncation (4 chars per token)
                text = text[:self.max_embedding_tokens * 4]
            
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error creating embedding: {str(e)}")
            raise
    
    def add_document(self, user_id: int, file_path: str, filename: str) -> KnowledgeDocument:
        """
        Add document with chunking and embeddings
        
        Process:
        1. Extract full text
        2. Split into chunks
        3. Create embedding for each chunk
        4. Store chunks in database
        """
        print(f"📄 Processing document: {filename}")
        
        # Extract text
        try:
            full_text = self.extract_text_from_file(file_path)
            print(f"📝 Extracted {len(full_text)} characters")
        except Exception as e:
            print(f"❌ Failed to extract text: {str(e)}")
            raise
        
        # Get file metadata
        file_size = os.path.getsize(file_path)
        file_type = filename.split('.')[-1].lower()
        content_preview = full_text[:500]
        
        # Create document record
        document = KnowledgeDocument(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            content_text=full_text,
            content_preview=content_preview,
            file_type=file_type,
            file_size=file_size,
            status="processing"
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        print(f"✅ Document created with ID: {document.id}")
        
        # Split into chunks
        try:
            chunks = self.split_text_into_chunks(full_text, self.chunk_size, self.chunk_overlap)
            print(f"✂️ Split into {len(chunks)} chunks")
            
            # Create embeddings and store chunks
            for idx, chunk_text in enumerate(chunks):
                print(f"   Processing chunk {idx + 1}/{len(chunks)}...", end="\r")
                
                # Generate embedding
                embedding = self.create_embedding(chunk_text)
                embedding_json = json.dumps(embedding)
                
                # Create chunk record
                chunk = KnowledgeChunk(
                    document_id=document.id,
                    chunk_index=idx,
                    chunk_text=chunk_text,
                    embedding_vector=embedding_json,
                    token_count=self.estimate_tokens(chunk_text)
                )
                self.db.add(chunk)
            
            # Update document status
            document.chunk_count = len(chunks)
            document.status = "ready"
            self.db.commit()
            
            print(f"\n✅ Document ready with {len(chunks)} chunks")
            
        except Exception as e:
            print(f"\n❌ Failed to process chunks: {str(e)}")
            document.status = "failed"
            self.db.commit()
            raise
        
        return document
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def search_documents(self, query: str, user_id: int, top_k: int = 5) -> List[str]:
        """
        Search for relevant chunks across all user documents
        
        Returns list of most relevant text chunks
        """
        print(f"🔍 Searching knowledge base for: {query[:50]}...")
        
        # Generate query embedding
        query_embedding = self.create_embedding(query)
        
        # Get all chunks for user's documents
        chunks = self.db.query(KnowledgeChunk).join(
            KnowledgeDocument
        ).filter(
            KnowledgeDocument.user_id == user_id,
            KnowledgeDocument.status == "ready"
        ).all()
        
        if not chunks:
            print("ℹ️ No knowledge chunks found")
            return []
        
        print(f"📚 Searching through {len(chunks)} chunks from {len(set(c.document_id for c in chunks))} documents")
        
        # Calculate similarities
        scored_chunks = []
        for chunk in chunks:
            try:
                chunk_embedding = json.loads(chunk.embedding_vector)
                similarity = self.cosine_similarity(query_embedding, chunk_embedding)
                scored_chunks.append({
                    'chunk': chunk,
                    'similarity': similarity,
                    'text': chunk.chunk_text,
                    'document_name': chunk.document.filename
                })
            except Exception as e:
                print(f"⚠️ Error processing chunk {chunk.id}: {str(e)}")
                continue
        
        # Sort by similarity and get top_k
        scored_chunks.sort(key=lambda x: x['similarity'], reverse=True)
        top_chunks = scored_chunks[:top_k]
        
        print(f"✅ Found {len(top_chunks)} relevant chunks:")
        for i, item in enumerate(top_chunks):
            print(f"   {i+1}. {item['document_name']} (similarity: {item['similarity']:.3f})")
        
        # Return just the text
        return [item['text'] for item in top_chunks]
    
    def get_context_from_documents(
        self, 
        query: str, 
        user_id: int, 
        max_tokens: int = 2000
    ) -> str:
        """
        Search for relevant documents and format context for AI
        
        Compatibility method for AI Agent Service.
        Returns formatted string with relevant document chunks.
        """
        relevant_chunks = self.search_documents(query, user_id, top_k=5)
        
        if not relevant_chunks:
            return ""
        
        # Format context for AI
        context_parts = []
        context_parts.append("=== RELEVANT KNOWLEDGE BASE DOCUMENTS ===\n")
        
        current_tokens = 0
        chunks_added = 0
        for i, chunk_text in enumerate(relevant_chunks):
            if not chunk_text or not chunk_text.strip():
                print(f"⚠️ Empty chunk {i+1}, skipping")
                continue
                
            chunk_tokens = self.estimate_tokens(chunk_text)
            print(f"📄 Chunk {i+1}: {chunk_tokens} tokens, {len(chunk_text)} chars")
            
            # Stop if we exceed max_tokens
            if current_tokens + chunk_tokens > max_tokens:
                print(f"⚠️ Token limit reached ({current_tokens + chunk_tokens} > {max_tokens}), stopping")
                break
            
            context_parts.append(f"\n--- Document Excerpt {i+1} ---")
            context_parts.append(chunk_text)
            current_tokens += chunk_tokens
            chunks_added += 1
        
        context = "\n".join(context_parts)
        print(f"📚 Prepared RAG context: {current_tokens} tokens from {chunks_added}/{len(relevant_chunks)} chunks")
        
        return context

