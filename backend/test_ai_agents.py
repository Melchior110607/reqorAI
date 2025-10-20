"""
Test script for AI Agent system
"""
import asyncio
import sys
sys.path.insert(0, '/app')

from app.database.config import SessionLocal
from app.models.intercepted_email import InterceptedEmail, EmailClassification
from app.models.request import Request, RequestType
from app.models.client import Client
from app.services.ai_agent_service import AIAgentService


def test_agent_1_response_to_request():
    """Test Agent 1: Response to Request"""
    print("\n" + "="*60)
    print("🧪 Testing Agent 1: RESPONSE_TO_REQUEST")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Find a test email classified as RESPONSE_TO_REQUEST
        email = db.query(InterceptedEmail).filter(
            InterceptedEmail.ai_classification == EmailClassification.RESPONSE_TO_REQUEST,
            InterceptedEmail.agent_processed == False
        ).first()
        
        if not email:
            print("⚠️ No RESPONSE_TO_REQUEST emails found to test")
            print("   Send a test email responding to an outgoing request first")
            return
        
        print(f"📧 Found test email: {email.id} - {email.subject}")
        print(f"   Classification: {email.ai_classification}")
        print(f"   Related requests: {email.related_request_ids}")
        
        # Process with agent
        agent_service = AIAgentService(db)
        result = agent_service.agent_response_to_request(email)
        
        print(f"\n✅ Agent 1 Result:")
        print(f"   Success: {result['success']}")
        print(f"   Message: {result['message']}")
        print(f"   Updated requests: {result.get('updated_requests', [])}")
        
        # Verify confirmations
        for request_id in result.get('updated_requests', []):
            request = db.query(Request).filter(Request.id == request_id).first()
            if request:
                print(f"\n   📋 Request {request_id}:")
                print(f"      Confirmed: {request.confirmation_received}")
                print(f"      Confirmed at: {request.confirmation_received_at}")
                print(f"      Details length: {len(request.confirmation_details or '')}")
        
    finally:
        db.close()


def test_agent_2_new_request():
    """Test Agent 2: New Request"""
    print("\n" + "="*60)
    print("🧪 Testing Agent 2: NEW_REQUEST")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Find a test email classified as NEW_REQUEST
        email = db.query(InterceptedEmail).filter(
            InterceptedEmail.ai_classification == EmailClassification.NEW_REQUEST,
            InterceptedEmail.agent_processed == False
        ).first()
        
        if not email:
            print("⚠️ No NEW_REQUEST emails found to test")
            print("   Send a test email with a new request first")
            return
        
        print(f"📧 Found test email: {email.id} - {email.subject}")
        print(f"   Classification: {email.ai_classification}")
        print(f"   Client ID: {email.client_id}")
        
        # Process with agent
        agent_service = AIAgentService(db)
        result = agent_service.agent_new_request(email)
        
        print(f"\n✅ Agent 2 Result:")
        print(f"   Success: {result['success']}")
        print(f"   Message: {result['message']}")
        print(f"   Request ID: {result.get('request_id')}")
        print(f"   Draft generated: {result.get('draft_generated')}")
        
        # Verify request creation
        if result.get('request_id'):
            request = db.query(Request).filter(Request.id == result['request_id']).first()
            if request:
                print(f"\n   📋 Created Request:")
                print(f"      ID: {request.id}")
                print(f"      Title: {request.title}")
                print(f"      Type: {request.type}")
                print(f"      Email Connection ID: {request.email_connection_id}")
                print(f"      Draft Response length: {len(request.draft_response or '')}")
                if request.draft_response:
                    print(f"\n   📝 Draft Response Preview:")
                    print(f"      {request.draft_response[:200]}...")
        
    finally:
        db.close()


def test_knowledge_base():
    """Test Knowledge Base"""
    print("\n" + "="*60)
    print("🧪 Testing Knowledge Base")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        from app.models.knowledge_base import KnowledgeDocument
        
        docs = db.query(KnowledgeDocument).all()
        
        print(f"📚 Found {len(docs)} knowledge document(s)")
        
        for doc in docs:
            print(f"\n   📄 Document {doc.id}:")
            print(f"      Filename: {doc.filename}")
            print(f"      Type: {doc.file_type}")
            print(f"      Size: {doc.file_size} bytes")
            print(f"      Text length: {len(doc.content_text or '')}")
            print(f"      Has embedding: {bool(doc.embedding_vector)}")
        
        if not docs:
            print("\n   ℹ️ Upload documents via /knowledge-base page to test RAG")
        
    finally:
        db.close()


def main():
    print("\n" + "="*60)
    print("🚀 AI AGENT SYSTEM TEST SUITE")
    print("="*60)
    
    test_knowledge_base()
    test_agent_1_response_to_request()
    test_agent_2_new_request()
    
    print("\n" + "="*60)
    print("✅ Tests completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()

