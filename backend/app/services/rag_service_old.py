"""
RAG (Retrieval-Augmented Generation) Service for knowledge base search
"""
import json
import numpy as np
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
import openai

from app.models.knowledge_base import KnowledgeDocument
from app.database.config import settings


class RAGService:
    def __init__(self, db: Session):
        self.db = db
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
    
    def create_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error creating embedding: {str(e)}")
            raise
    
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
    
    def search_relevant_documents(
        self, 
        query: str, 
        user_id: int, 
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find most relevant documents using cosine similarity
        
        Returns list of dicts with:
        - document: KnowledgeDocument object
        - similarity: float score
        - relevant_chunk: str (excerpt from content)
        """
        # Generate query embedding
        query_embedding = self.create_embedding(query)
        
        # Get all user documents
        documents = self.db.query(KnowledgeDocument).filter(
            KnowledgeDocument.user_id == user_id
        ).all()
        
        if not documents:
            print(f"ℹ️ No knowledge documents found for user {user_id}")
            return []
        
        # Calculate similarity scores
        results = []
        for doc in documents:
            if not doc.embedding_vector:
                continue
            
            try:
                doc_embedding = json.loads(doc.embedding_vector)
                similarity = self.cosine_similarity(query_embedding, doc_embedding)
                
                # Extract relevant chunk (first 500 characters as preview)
                chunk = doc.content_text[:500] if doc.content_text else ""
                
                results.append({
                    'document': doc,
                    'similarity': similarity,
                    'relevant_chunk': chunk,
                    'filename': doc.filename,
                    'file_type': doc.file_type
                })
            except Exception as e:
                print(f"⚠️ Error processing document {doc.id}: {str(e)}")
                continue
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = results[:top_k]
        
        print(f"📚 Found {len(top_results)} relevant documents for query")
        for i, result in enumerate(top_results):
            print(f"  {i+1}. {result['filename']} (similarity: {result['similarity']:.3f})")
        
        return top_results
    
    def get_context_from_documents(
        self, 
        query: str, 
        user_id: int, 
        max_tokens: int = 2000
    ) -> str:
        """
        Search for relevant documents and format context for AI
        """
        relevant_docs = self.search_relevant_documents(query, user_id, top_k=3)
        
        if not relevant_docs:
            return ""
        
        context_parts = []
        context_parts.append("=== RELEVANT KNOWLEDGE BASE DOCUMENTS ===\n")
        
        for i, doc_info in enumerate(relevant_docs):
            doc = doc_info['document']
            context_parts.append(f"\n--- Document {i+1}: {doc.filename} ---")
            
            # Add content (truncated if needed)
            content = doc.content_text or ""
            if len(content) > 1500:
                content = content[:1500] + "...[truncated]"
            
            context_parts.append(content)
        
        context = "\n".join(context_parts)
        return context

