"""
AI Agent Service - Processes classified emails and takes automated actions
"""
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import openai

from app.models.intercepted_email import InterceptedEmail, EmailClassification
from app.models.request import Request, RequestType, RequestStatus, RequestPriority
from app.models.client import Client
from app.models.user import User
from app.database.config import settings
from app.services.rag_service import RAGService


class AIAgentService:
    def __init__(self, db: Session):
        self.db = db
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.rag_service = RAGService(db)
    
    def process_classified_email(self, email: InterceptedEmail) -> Dict[str, Any]:
        """Route to appropriate agent based on classification"""
        try:
            if email.ai_classification == EmailClassification.RESPONSE_TO_REQUEST:
                return self.agent_response_to_request(email)
            elif email.ai_classification == EmailClassification.NEW_REQUEST:
                return self.agent_new_request(email)
            elif email.ai_classification == EmailClassification.CONFIRMATION:
                return self.agent_confirmation(email)
            elif email.ai_classification == EmailClassification.CLIENT_REMINDER:
                return self.agent_client_reminder(email)
            elif email.ai_classification == EmailClassification.DISSATISFACTION:
                return self.agent_dissatisfaction(email)
            elif email.ai_classification == EmailClassification.MIXED:
                return self.agent_mixed(email)
            else:
                return {
                    'success': False,
                    'message': f'No agent implemented for classification: {email.ai_classification}'
                }
        except Exception as e:
            print(f"❌ Agent processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def agent_response_to_request(self, email: InterceptedEmail) -> Dict[str, Any]:
        """
        Agent 1: Updates OUTGOING request as confirmed
        (Client confirms they received our request)
        """
        print(f"🤖 Agent 1: Processing RESPONSE_TO_REQUEST for email {email.id}")
        
        # Get related request IDs
        related_request_ids = []
        if email.related_request_ids:
            try:
                related_request_ids = json.loads(email.related_request_ids)
            except:
                related_request_ids = []
        
        if not related_request_ids:
            print(f"⚠️ No related requests found in email {email.id}")
            return {'success': False, 'message': 'No related requests found'}
        
        updated_requests = []
        
        for request_id in related_request_ids:
            request = self.db.query(Request).filter(
                Request.id == request_id,
                Request.user_id == email.user_id
            ).first()
            
            if not request:
                print(f"⚠️ Request {request_id} not found")
                continue
            
            # Only handle OUTGOING requests
            if request.type != RequestType.OUTGOING:
                print(f"ℹ️ Skipping non-outgoing request {request_id}")
                continue
            
            request.confirmation_received = True
            request.confirmation_received_at = datetime.now(timezone.utc)
            request.confirmation_details = email.body
            updated_requests.append(request.id)
            print(f"✅ Updated OUTGOING request {request.id} as confirmed")
        
        # Mark email as agent_processed
        email.agent_processed = True
        email.agent_action_taken = f"Agent 1: Confirmed {len(updated_requests)} outgoing request(s)"
        
        self.db.commit()
        
        return {
            'success': True,
            'agent': 'response_to_request',
            'updated_requests': updated_requests,
            'message': f'Confirmed {len(updated_requests)} outgoing request(s)'
        }
    
    def agent_confirmation(self, email: InterceptedEmail) -> Dict[str, Any]:
        """
        Agent CONFIRMATION: Handles INCOMING request confirmations
        (Client confirms they are satisfied with our response)
        
        Actions:
        1. Mark request as confirmed
        2. Clear any client reminders (they're satisfied!)
        3. Mark request as COMPLETED
        """
        print(f"🤖 Agent CONFIRMATION: Processing CONFIRMATION for email {email.id}")
        
        # Get related request IDs
        related_request_ids = []
        if email.related_request_ids:
            try:
                related_request_ids = json.loads(email.related_request_ids)
            except:
                related_request_ids = []
        
        if not related_request_ids:
            print(f"⚠️ No related requests found in email {email.id}")
            return {'success': False, 'message': 'No related requests found'}
        
        updated_requests = []
        
        for request_id in related_request_ids:
            request = self.db.query(Request).filter(
                Request.id == request_id,
                Request.user_id == email.user_id
            ).first()
            
            if not request:
                print(f"⚠️ Request {request_id} not found")
                continue
            
            # Only handle INCOMING requests
            if request.type != RequestType.INCOMING:
                print(f"ℹ️ Skipping non-incoming request {request_id}")
                continue
            
            print(f"📋 Processing INCOMING request {request.id}: {request.title}")
            
            # 1. Mark as confirmed
            request.confirmation_received = True
            request.confirmation_received_at = datetime.now(timezone.utc)
            request.confirmation_details = email.body
            print(f"   ✓ Marked as confirmed")
            
            # 2. Clear any previous client reminders (they're satisfied now!)
            if request.follow_up_type or request.follow_up_count > 0:
                print(f"   🧹 Clearing {request.follow_up_count} previous reminder(s)")
                request.follow_up_type = None
                request.follow_up_count = 0
                request.latest_follow_up_message = None
                request.latest_follow_up_at = None
            
            # 3. Mark as COMPLETED since client is satisfied
            old_status = request.status
            request.status = RequestStatus.COMPLETED
            print(f"   ✓ Status updated: {old_status} → COMPLETED")
            
            updated_requests.append(request.id)
            print(f"✅ Confirmation complete for request {request.id}")
        
        # Mark email as agent_processed
        email.agent_processed = True
        email.agent_action_taken = f"Agent CONFIRMATION: Confirmed {len(updated_requests)} incoming request(s)"
        
        self.db.commit()
        
        return {
            'success': True,
            'agent': 'confirmation',
            'updated_requests': updated_requests,
            'message': f'Confirmed and completed {len(updated_requests)} incoming request(s)'
        }
    
    def agent_new_request(self, email: InterceptedEmail) -> Dict[str, Any]:
        """
        Agent 2: Creates incoming request and generates draft response using RAG
        """
        print(f"🤖 Agent 2: Processing NEW_REQUEST for email {email.id}")
        
        # Get client info
        client = self.db.query(Client).filter(
            Client.id == email.client_id
        ).first()
        
        if not client:
            return {'success': False, 'message': 'No client associated with email'}
        
        # Extract title from subject or first line of body
        title = email.subject if email.subject else (email.body[:100] + "...")
        
        # Extract due date using AI
        due_date = self._extract_due_date(email)
        
        # Create new incoming request
        new_request = Request(
            title=title,
            description=email.body,  # Store original body with PII for user
            type=RequestType.INCOMING,
            status=RequestStatus.PENDING,
            priority=RequestPriority.MEDIUM,
            client_id=email.client_id,
            user_id=email.user_id,
            email_connection_id=email.connection_id,  # Link to receiving email connection
            due_date=due_date  # AI-extracted due date
        )

    
        
        self.db.add(new_request)
        self.db.flush()  # Get the ID
        
        print(f"📝 Created incoming request {new_request.id}: {title}")
        
        # Generate draft response using RAG
        try:
            draft_response = self._generate_draft_response(
                email=email,
                client=client,      
                user_id=email.user_id
            )
            
            new_request.draft_response = draft_response
            new_request.draft_generated_at = datetime.now(timezone.utc)
            
            print(f"✍️ Generated draft response ({len(draft_response)} chars)")
        except Exception as e:
            print(f"⚠️ Failed to generate draft response: {str(e)}")
            # Continue anyway - request is created, just without draft
        
        # Mark email as agent_processed
        email.agent_processed = True
        email.agent_action_taken = f"Agent 2: Created incoming request {new_request.id}"
        
        # Link email to request
        if email.related_request_ids:
            try:
                existing_ids = json.loads(email.related_request_ids)
                existing_ids.append(new_request.id)
                email.related_request_ids = json.dumps(existing_ids)
            except:
                email.related_request_ids = json.dumps([new_request.id])
        else:
            email.related_request_ids = json.dumps([new_request.id])
        
        self.db.commit()
        
        return {
            'success': True,
            'agent': 'new_request',
            'request_id': new_request.id,
            'draft_generated': bool(new_request.draft_response),
            'message': f'Created incoming request {new_request.id}'
        }
    
    def _extract_due_date(self, email: InterceptedEmail) -> Optional[datetime]:
        """
        Extract due date from email using AI
        Returns None if no due date is mentioned
        """
        try:
            system_prompt = """You are a date extraction assistant. 
Your task is to extract any deadline, due date, or delivery date mentioned in the email.

IMPORTANT:
- If a date is mentioned, return it in ISO format: YYYY-MM-DD
- If no date is mentioned, return: "NONE"
- Consider phrases like: "by next Monday", "deadline is March 15", "need it before Friday", "due on..."
- Today's date for reference: {today}
- If only a day is mentioned (like "Monday"), assume it's the next occurrence of that day

Return ONLY the date in YYYY-MM-DD format or "NONE" - no other text."""
            
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            system_prompt = system_prompt.format(today=today)
            
            user_prompt = f"""Email Subject: {email.subject}

Email Body:
{email.body}

Extract the due date (return YYYY-MM-DD or "NONE")."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,  # Deterministic
                max_tokens=50
            )
            
            extracted = response.choices[0].message.content.strip()
            print(f"📅 AI extracted due date: {extracted}")
            
            if extracted.upper() == "NONE":
                return None
            
            # Parse the date
            try:
                # Try parsing ISO format
                parsed_date = datetime.strptime(extracted, "%Y-%m-%d")
                # Set time to end of day (23:59:59)
                parsed_date = parsed_date.replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                return parsed_date
            except ValueError:
                print(f"⚠️ Could not parse extracted date: {extracted}")
                return None
                
        except Exception as e:
            print(f"❌ Error extracting due date: {str(e)}")
            return None
    
    def _generate_draft_response(
        self, 
        email: InterceptedEmail, 
        client: Client,
        user_id: int
    ) -> str:
        """Generate draft response using OpenAI with RAG context"""
        
        # Get user signature
        user = self.db.query(User).filter(User.id == user_id).first()
        user_signature = user.email_signature if user and user.email_signature else ""
        
        # Get relevant knowledge base context
        rag_context = self.rag_service.get_context_from_documents(
            query=email.anonymized_body,  # Use anonymized version for RAG search
            user_id=user_id,
            max_tokens=2000
        )
        
        # Prepare system prompt
        signature_note = """

IMPORTANT: The user has configured an email signature. DO NOT include any closing (like "Best regards", "Sincerely", name, title, etc.) in your response. The signature will be automatically appended after your message.""" if user_signature else ""
        
        system_prompt = f"""You are a professional business email assistant. 
Your task is to draft a response to a client's request.

CLIENT INFORMATION:
- Name: {client.name}
- Company: {client.company}
- Email: {client.email}

{signature_note}

Write a professional, helpful, and courteous response. Be concise but complete.
If knowledge base documents are provided, use them to give accurate information.
If you don't have enough information, politely indicate what additional details you need.

Format the response as a complete email body (without subject line or greeting, and WITHOUT closing/signature if one is configured)."""
        
        # Prepare user prompt
        user_prompt = f"""CLIENT'S REQUEST:
Subject: {email.subject}

{email.anonymized_body}

{rag_context if rag_context else ""}

Please draft a professional response to this request."""
        
        # Call OpenAI
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=5000
        )
        
        draft = response.choices[0].message.content
        
        # Append signature if configured
        if user_signature:
            draft = f"{draft}\n\n{user_signature}"
        
        return draft
    
    def regenerate_draft_response(self, request_id: int, user_id: int) -> Dict[str, Any]:
        """Regenerate draft response for an existing request"""
        request = self.db.query(Request).filter(
            Request.id == request_id,
            Request.user_id == user_id
        ).first()
        
        if not request:
            return {'success': False, 'message': 'Request not found'}
        
        if request.type != RequestType.INCOMING:
            return {'success': False, 'message': 'Can only generate drafts for incoming requests'}
        
        # Get client
        client = self.db.query(Client).filter(
            Client.id == request.client_id
        ).first()
        
        if not client:
            return {'success': False, 'message': 'Client not found'}
        
        # Create a pseudo-email for draft generation
        class PseudoEmail:
            def __init__(self, request):
                self.subject = request.title
                self.body = request.description
                self.anonymized_body = request.description
        
        try:
            draft = self._generate_draft_response(
                email=PseudoEmail(request),
                client=client,
                user_id=user_id
            )
            
            request.draft_response = draft
            request.draft_generated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            return {
                'success': True,
                'draft_response': draft,
                'message': 'Draft response regenerated'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def agent_client_reminder(self, email: InterceptedEmail) -> Dict[str, Any]:
        """
        Agent 3: Handle CLIENT_REMINDER (client redemande la même chose)
        
        Updates the existing incoming request to HIGH priority and increments follow-up count.
        Does NOT create a new request, just marks the existing one as having a client reminder.
        """
        print(f"🤖 Agent 3: Processing CLIENT_REMINDER for email {email.id}")
        
        # PRIORITY 1: Use AI-identified related_request_ids if available
        parent_request = None
        if email.related_request_ids:
            try:
                related_ids = json.loads(email.related_request_ids)
                if related_ids:
                    # Get the first related request (AI identified this as the parent)
                    parent_request = self.db.query(Request).filter(
                        Request.id == related_ids[0],
                        Request.user_id == email.user_id
                    ).first()
                    if parent_request:
                        print(f"📎 Using AI-identified parent request: {parent_request.id}")
            except:
                pass
        
        # FALLBACK: If no AI-identified parent, use heuristic search
        if not parent_request:
            print(f"🔍 No AI-identified parent, searching by similarity...")
            parent_request = self._find_parent_request_for_reminder(email)
        
        if not parent_request:
            print(f"⚠️ No parent request found for client reminder, treating as NEW_REQUEST")
            # Fallback: treat as new request
            return self.agent_new_request(email)
        
        print(f"📎 Found request to update: {parent_request.id} - {parent_request.title}")
        
        # Update the existing request (NO description modification - displayed in UI separately)
        parent_request.priority = RequestPriority.HIGH  # Elevate to HIGH
        parent_request.follow_up_count = (parent_request.follow_up_count or 0) + 1
        parent_request.follow_up_type = 'client_reminder'  # Mark as having client reminder
        
        # Store the latest follow-up message for UI display
        parent_request.latest_follow_up_message = email.body  # Original email with PII for user to see
        parent_request.latest_follow_up_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        print(f"✅ Updated request {parent_request.id}: Priority → HIGH, Follow-up count → {parent_request.follow_up_count}")
        
        # Mark email as processed
        email.agent_processed = True
        email.agent_action_taken = f"Agent 3: Updated request {parent_request.id} - CLIENT_REMINDER (follow-up #{parent_request.follow_up_count})"
        
        # Link email to request
        if email.related_request_ids:
            try:
                existing_ids = json.loads(email.related_request_ids)
                if parent_request.id not in existing_ids:
                    existing_ids.append(parent_request.id)
                    email.related_request_ids = json.dumps(existing_ids)
            except:
                email.related_request_ids = json.dumps([parent_request.id])
        else:
            email.related_request_ids = json.dumps([parent_request.id])
        
        self.db.commit()
        
        return {
            'success': True,
            'message': f'Request {parent_request.id} updated with client reminder',
            'request_id': parent_request.id,
            'follow_up_count': parent_request.follow_up_count,
            'new_priority': 'high'
        }
    
    def agent_dissatisfaction(self, email: InterceptedEmail) -> Dict[str, Any]:
        """
        Agent 4: Handle DISSATISFACTION (client insatisfait de la réponse)
        
        Updates the existing incoming request to URGENT priority and regenerates an enhanced response.
        Does NOT create a new request, just updates the existing one with more detailed information.
        """
        print(f"🤖 Agent 4: Processing DISSATISFACTION for email {email.id}")
        
        # PRIORITY 1: Use AI-identified related_request_ids if available
        parent_request = None
        if email.related_request_ids:
            try:
                related_ids = json.loads(email.related_request_ids)
                if related_ids:
                    # Get the first related request (AI identified this as the parent)
                    parent_request = self.db.query(Request).filter(
                        Request.id == related_ids[0],
                        Request.user_id == email.user_id
                    ).first()
                    if parent_request:
                        print(f"📎 Using AI-identified parent request: {parent_request.id}")
            except:
                pass
        
        # FALLBACK: If no AI-identified parent, use heuristic search
        if not parent_request:
            print(f"🔍 No AI-identified parent, searching by dissatisfaction heuristic...")
            parent_request = self._find_parent_request_for_dissatisfaction(email)
        
        if not parent_request:
            print(f"⚠️ No parent request found for dissatisfaction, treating as NEW_REQUEST")
            return self.agent_new_request(email)
        
        print(f"📎 Found request to update: {parent_request.id} - {parent_request.title}")
        
        # Update the existing request (NO description modification - displayed in UI separately)
        parent_request.priority = RequestPriority.URGENT  # Elevate to URGENT (highest)
        parent_request.follow_up_count = (parent_request.follow_up_count or 0) + 1
        parent_request.follow_up_type = 'dissatisfaction'  # Mark as dissatisfaction
        
        # Store the latest follow-up message for UI display
        parent_request.latest_follow_up_message = email.body  # Original email with PII for user to see
        parent_request.latest_follow_up_at = datetime.now(timezone.utc)
        
        # Generate ENHANCED draft response with MORE context from RAG
        client = self.db.query(Client).filter(Client.id == email.client_id).first()
        if client:
            try:
                enhanced_draft = self._generate_enhanced_response(email, parent_request, client)
                parent_request.draft_response = enhanced_draft
                parent_request.draft_generated_at = datetime.now(timezone.utc)
                print(f"✅ Generated enhanced draft with more RAG context")
            except Exception as e:
                print(f"⚠️ Failed to generate enhanced draft: {str(e)}")
        
        self.db.commit()
        
        print(f"✅ Updated request {parent_request.id}: Priority → URGENT, Follow-up count → {parent_request.follow_up_count}")
        
        # Mark email as processed
        email.agent_processed = True
        email.agent_action_taken = f"Agent 4: Updated request {parent_request.id} - DISSATISFACTION (follow-up #{parent_request.follow_up_count})"
        
        # Link email to request
        if email.related_request_ids:
            try:
                existing_ids = json.loads(email.related_request_ids)
                if parent_request.id not in existing_ids:
                    existing_ids.append(parent_request.id)
                    email.related_request_ids = json.dumps(existing_ids)
            except:
                email.related_request_ids = json.dumps([parent_request.id])
        else:
            email.related_request_ids = json.dumps([parent_request.id])
        
        self.db.commit()
        
        return {
            'success': True,
            'message': f'Request {parent_request.id} updated with dissatisfaction - enhanced response generated',
            'request_id': parent_request.id,
            'follow_up_count': parent_request.follow_up_count,
            'new_priority': 'urgent'
        }
    
    def _find_parent_request_for_reminder(self, email: InterceptedEmail) -> Optional[Request]:
        """
        Find parent request for CLIENT_REMINDER
        
        Logic: Same client + similar subject/keywords + recent (last 30 days)
        """
        # Get recent requests from same client
        recent_requests = self.db.query(Request).filter(
            Request.client_id == email.client_id,
            Request.user_id == email.user_id,
            Request.type == RequestType.INCOMING,
            Request.created_at >= datetime.now(timezone.utc) - timedelta(days=30)
        ).order_by(Request.created_at.desc()).all()
        
        if not recent_requests:
            return None
        
        # Simple heuristic: find request with most similar title
        from difflib import SequenceMatcher
        
        best_match = None
        best_similarity = 0.0
        
        email_subject_lower = email.subject.lower()
        
        for req in recent_requests:
            similarity = SequenceMatcher(None, email_subject_lower, req.title.lower()).ratio()
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = req
        
        # Require at least 50% similarity
        if best_similarity >= 0.5:
            return best_match
        
        # If no good match, return most recent
        return recent_requests[0] if recent_requests else None
    
    def _find_parent_request_for_dissatisfaction(self, email: InterceptedEmail) -> Optional[Request]:
        """
        Find parent request for DISSATISFACTION
        
        Logic: Recent request from same client that has a draft_response (we responded already)
        """
        # Look for recent requests where we sent a response
        recent_requests = self.db.query(Request).filter(
            Request.client_id == email.client_id,
            Request.user_id == email.user_id,
            Request.type == RequestType.INCOMING,
            Request.draft_response.isnot(None),  # We responded
            Request.created_at >= datetime.now(timezone.utc) - timedelta(days=7)  # Last week
        ).order_by(Request.created_at.desc()).all()
        
        # Return most recent
        return recent_requests[0] if recent_requests else None
    
    def _generate_enhanced_response(self, email: InterceptedEmail, parent_request: Request, client: Client) -> str:
        """
        Generate ENHANCED response for DISSATISFACTION with MORE RAG context
        """
        try:
            # Get user signature
            user = self.db.query(User).filter(User.id == email.user_id).first()
            user_signature = user.email_signature if user and user.email_signature else ""
            
            # Get MORE context from knowledge base (top 10 chunks instead of 5)
            rag_context = self.rag_service.get_context_from_documents(
                query=f"{parent_request.title} {email.anonymized_body}",
                user_id=email.user_id,
                max_tokens=3000  # More tokens for enhanced response
            )
            
            signature_note = "\n\nIMPORTANT: The user has configured an email signature. DO NOT include any closing (like 'Best regards', 'Sincerely', name, title, etc.). The signature will be automatically appended." if user_signature else ""
            
            system_prompt = f"""You are a professional business assistant.
The client was dissatisfied with the previous response and needs MORE detailed information.

Your response should:
- Apologize for the insufficient previous response
- Provide MUCH MORE DETAIL using the knowledge base
- Address their specific concerns
- Be thorough and comprehensive
- Maintain a helpful, professional tone
- Be 2-3 paragraphs{signature_note}"""
            
            user_prompt = f"""CLIENT: {client.company}
ORIGINAL REQUEST: {parent_request.title}
PREVIOUS RESPONSE: {parent_request.draft_response}
CLIENT'S DISSATISFACTION MESSAGE: {email.anonymized_body}

{rag_context if rag_context else "Note: No additional knowledge base context available."}

Generate an enhanced, more detailed response addressing their concerns."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            draft = response.choices[0].message.content
            
            # Append signature if configured
            if user_signature:
                draft = f"{draft}\n\n{user_signature}"
            
            return draft
            
        except Exception as e:
            print(f"❌ Error generating enhanced response: {str(e)}")
            fallback = "We apologize for the insufficient information in our previous response. Let us provide more detailed information to address your concerns."
            user = self.db.query(User).filter(User.id == email.user_id).first()
            if user and user.email_signature:
                fallback = f"{fallback}\n\n{user.email_signature}"
            return fallback
    
    def agent_mixed(self, email: InterceptedEmail) -> Dict[str, Any]:
        """
        Agent 5: Handle MIXED emails (multiple classifications in one email)
        
        Processes each sub-classification by calling the appropriate agent.
        For example: Email contains both a new request AND a response to an existing request.
        """
        print(f"🤖 Agent 5: Processing MIXED email {email.id}")
        
        # Get sub-classifications
        if not email.ai_sub_classifications:
            return {
                'success': False,
                'message': 'MIXED classification but no sub_classifications found'
            }
        
        try:
            sub_classifications = json.loads(email.ai_sub_classifications)
        except json.JSONDecodeError:
            return {
                'success': False,
                'message': 'Failed to parse sub_classifications JSON'
            }
        
        if not sub_classifications:
            return {
                'success': False,
                'message': 'MIXED classification but sub_classifications is empty'
            }
        
        print(f"📋 Processing {len(sub_classifications)} sub-classifications")
        
        results = []
        created_requests = []  # Track requests created during processing
        
        # Store original email data to restore later
        original_classification = email.ai_classification
        original_related_ids = email.related_request_ids
        original_body = email.body
        original_anonymized_body = email.anonymized_body
        
        for i, sub in enumerate(sub_classifications):
            classification = sub.get('classification')
            related_requests = sub.get('related_requests', [])
            email_segment = sub.get('email_segment', '')
            
            # 🔗 IMPORTANT: If previous agents created requests, add them to related_requests
            # This ensures CLIENT_REMINDER can find the request created by NEW_REQUEST
            if created_requests and classification in [
                EmailClassification.CLIENT_REMINDER.value,
                EmailClassification.DISSATISFACTION.value
            ]:
                related_requests.extend(created_requests)
                print(f"  🔗 Added {len(created_requests)} newly created requests to related_requests")
            
            print(f"  {i+1}. {classification} (related requests: {related_requests})")
            print(f"     Email segment: {email_segment[:100]}...")
            
            # Create a segmented version of the email with ONLY this part
            # The agent will work on this specific segment
            # BUT we keep the original full email in body for the user to see
            
            # Temporarily modify email with the segmented content
            email.ai_classification = EmailClassification(classification)
            email.related_request_ids = json.dumps(related_requests)
            
            # For agents that use anonymized_body (AI processing), use the segment
            # This will be anonymized by the agent if needed
            email.anonymized_body = email_segment
            
            # Keep original body for user reference (will be stored in request description)
            # But add a note about which part is relevant
            email.body = f"{email_segment}\n\n[ORIGINAL EMAIL - Full Context]\n{original_body}"
            
            # Route to appropriate agent
            try:
                if classification == EmailClassification.RESPONSE_TO_REQUEST.value:
                    result = self.agent_response_to_request(email)
                elif classification == EmailClassification.NEW_REQUEST.value:
                    result = self.agent_new_request(email)
                    # Track the created request ID
                    print(f"  📊 NEW_REQUEST result: success={result.get('success')}, request_id={result.get('request_id')}")
                    if result.get('success') and result.get('request_id'):
                        created_requests.append(result['request_id'])
                        print(f"  ✅ Created request #{result['request_id']}, added to tracking (total: {len(created_requests)})")
                    else:
                        print(f"  ⚠️ NEW_REQUEST did not return request_id, cannot track")
                elif classification == EmailClassification.CONFIRMATION.value:
                    result = self.agent_confirmation(email)
                elif classification == EmailClassification.CLIENT_REMINDER.value:
                    result = self.agent_client_reminder(email)
                elif classification == EmailClassification.DISSATISFACTION.value:
                    result = self.agent_dissatisfaction(email)
                else:
                    result = {
                        'success': False,
                        'message': f'No agent for classification: {classification}'
                    }
                
                results.append({
                    'classification': classification,
                    'result': result,
                    'email_segment': email_segment[:200] + "..." if len(email_segment) > 200 else email_segment
                })
                
            except Exception as e:
                print(f"  ❌ Error processing sub-classification {classification}: {str(e)}")
                import traceback
                print(traceback.format_exc())
                results.append({
                    'classification': classification,
                    'result': {
                        'success': False,
                        'error': str(e)
                    },
                    'email_segment': email_segment[:200] + "..."
                })
        
        # Restore original email values
        email.ai_classification = original_classification
        email.related_request_ids = original_related_ids
        email.body = original_body
        email.anonymized_body = original_anonymized_body
        
        # Mark email as processed
        email.agent_processed = True
        email.agent_action_taken = f"Agent 5: Processed MIXED email with {len(results)} sub-classifications"
        self.db.commit()
        
        # Count successes
        successful = sum(1 for r in results if r['result'].get('success', False))
        
        print(f"✅ MIXED processing complete: {successful}/{len(results)} successful")
        
        return {
            'success': True,
            'message': f'Processed {len(results)} sub-classifications ({successful} successful)',
            'results': results,
            'sub_classification_count': len(results)
        }

