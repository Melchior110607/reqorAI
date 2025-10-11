import json
import openai
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.intercepted_email import InterceptedEmail, EmailClassification, ProcessingStatus
from app.models.request import Request
from app.database.config import settings
from sqlalchemy.sql import func

class AIClassificationService:
    def __init__(self, db: Session):
        self.db = db
        self.client = openai.OpenAI(api_key=settings.openai_api_key)

    def classify_email(self, intercepted_email: InterceptedEmail) -> Dict[str, Any]:
        """Classifie un email intercepté avec l'IA"""
        
        # Récupérer les demandes liées au client
        outgoing_requests = []
        incoming_requests = []
        
        if intercepted_email.client_id:
            outgoing_requests = self.db.query(Request).filter(
                Request.client_id == intercepted_email.client_id,
                Request.type == "outgoing",
                Request.user_id == intercepted_email.user_id
            ).all()
            
            
            incoming_requests = self.db.query(Request).filter(
                Request.client_id == intercepted_email.client_id,
                Request.type == "incoming",
                Request.user_id == intercepted_email.user_id
            ).all()
            

        # Préparer le contexte pour l'IA
        context = self._prepare_context(intercepted_email, outgoing_requests, incoming_requests)
        
        # Appel à l'IA
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": context}
                ],
                temperature=0.1,
                max_tokens=5000
            )
            
            result = self._parse_ai_response(response.choices[0].message.content)

        
            
            # Mettre à jour l'email intercepté
            intercepted_email.ai_classification = result['classification']
            intercepted_email.ai_confidence = result['confidence']
            intercepted_email.ai_reasoning = result['reasoning']
            intercepted_email.related_request_ids = json.dumps(result['related_requests'])
            intercepted_email.processing_status = ProcessingStatus.COMPLETED
            intercepted_email.processed_at = func.now()
            
            self.db.commit()
            
            return result
            
        except Exception as e:
            intercepted_email.processing_status = ProcessingStatus.FAILED
            intercepted_email.error_message = str(e)
            self.db.commit()
            raise e

    def _get_system_prompt(self) -> str:
        """System prompt for email classification"""
        return """
You are an AI assistant specializing in analyzing B2B emails for a request management system.

Your task is to classify each email according to these EXACT categories. You MUST use the exact category name:

1. response_to_request: Email is responding to one of our OUTGOING requests (we asked them for something)
2. new_request: New customer request that does NOT relate to any existing incoming/outgoing requests
3. confirmation: Customer confirms they received our response
4. client_reminder: Customer is following up / reminding us about an INCOMING request (they asked us for something and we haven't responded yet)
5. dissatisfaction: Customer expresses dissatisfaction or requests additional information
6. mixed: Email contains multiple types above OR multiple requests
7. unclassified: ONLY use this if the email is completely unrelated to business (spam, personal chat, etc.)

CRITICAL RULES:
- If the email relates to ANY existing request, DO NOT use "unclassified"
- A follow-up on an existing incoming request = "client_reminder"
- A response to our outgoing request = "response_to_request"
- "unclassified" means the email has NO business purpose
- Always link related request IDs in the related_requests array

Respond ONLY in valid JSON format (no markdown, no code blocks):
{
  "classification": "response_to_request",
  "confidence": 0.95,
  "reasoning": "Clear explanation of why this classification was chosen",
  "related_requests": [1, 2]
}

Valid classification values: response_to_request, new_request, confirmation, client_reminder, dissatisfaction, mixed, unclassified
"""

    def _prepare_context(self, email: InterceptedEmail, outgoing: List[Request], incoming: List[Request]) -> str:
        """Prépare le contexte pour l'IA"""
        
        outgoing_context = []
        for req in outgoing:
            outgoing_context.append({
                "id": req.id,
                "title": req.title,
                "description": req.description,
                "status": req.status,
                "created_at": req.created_at.isoformat(),
                "due_date": req.due_date.isoformat() if req.due_date else None
            })
        
        incoming_context = []
        for req in incoming:
            incoming_context.append({
                "id": req.id,
                "title": req.title,
                "description": req.description,
                "status": req.status,
                "created_at": req.created_at.isoformat(),
                "due_date": req.due_date.isoformat() if req.due_date else None
            })
        
        context = f"""
EMAIL TO ANALYZE:
From: {email.sender_email} ({email.sender_name})
Subject: {email.subject}
Content: {email.body}
Received: {email.email_received_at.isoformat()}

EXISTING OUTGOING REQUESTS (our requests to this client - we asked them for something):
{json.dumps(outgoing_context, indent=2, ensure_ascii=False)}

EXISTING INCOMING REQUESTS (this client's requests to us - they asked us for something):
{json.dumps(incoming_context, indent=2, ensure_ascii=False)}

INSTRUCTIONS:
1. Carefully read the email content
2. Check if it relates to ANY existing request (outgoing or incoming)
3. If it relates to an existing request, classify accordingly (NOT unclassified)
4. Only use "unclassified" if the email has NO business purpose (spam, personal chat, etc.)
5. For your example: A follow-up on request ID 6 should be "client_reminder", NOT "unclassified"
"""
        return context

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse la réponse de l'IA"""
        try:
            # Nettoyer la réponse (enlever les backticks markdown si présents)
            cleaned_response = response_text.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            result = json.loads(cleaned_response)

            
            # Validation des champs requis
            required_fields = ['classification', 'confidence', 'reasoning', 'related_requests']
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validation de la classification
            valid_classifications = [e.value for e in EmailClassification]
            if result['classification'] not in valid_classifications:
                result['classification'] = EmailClassification.UNCLASSIFIED.value
            
            # Validation du score de confiance
            if not isinstance(result['confidence'], (int, float)) or not (0 <= result['confidence'] <= 1):
                result['confidence'] = 0.0
            
            # Validation des demandes liées
            if not isinstance(result['related_requests'], list):
                result['related_requests'] = []
            
            return result
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback en cas d'erreur de parsing
            return {
                'classification': EmailClassification.UNCLASSIFIED.value,
                'confidence': 0.0,
                'reasoning': f'Erreur de parsing de la réponse IA: {str(e)}',
                'related_requests': []
            }
