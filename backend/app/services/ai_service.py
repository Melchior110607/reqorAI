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
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": context}
                ],
                temperature=0.1,
                max_tokens=1000
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
        """Prompt système pour la classification"""
        return """
Vous êtes un assistant IA spécialisé dans l'analyse d'emails B2B pour un système de gestion de demandes.

Votre tâche est de classifier chaque email selon ces catégories EXACTES :
1. RESPONSE_TO_REQUEST : Email répond à une de nos demandes sortantes
2. NEW_REQUEST : Nouvelle demande du client (créer incoming request)
3. CONFIRMATION : Confirmation de réception de notre réponse
4. CLIENT_REMINDER : Client relance sur une demande entrante
5. DISSATISFACTION : Insatisfaction ou demande d'infos supplémentaires
6. MIXED : Combinaison de plusieurs types ci-dessus
7. UNCLASSIFIED : Ne correspond à aucune catégorie

Analysez le contenu, le contexte des demandes existantes, et fournissez :
- Classification (une des catégories ci-dessus)
- Score de confiance (0.0 à 1.0)
- Raisonnement détaillé
- IDs des demandes liées (si applicable)

Répondez UNIQUEMENT en format JSON valide :
{
  "classification": "CATEGORY",
  "confidence": 0.85,
  "reasoning": "Explication détaillée...",
  "related_requests": [1, 2, 3]
}
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
EMAIL À ANALYSER :
De: {email.sender_email} ({email.sender_name})
Sujet: {email.subject}
Contenu: {email.body}
Reçu le: {email.email_received_at.isoformat()}

DEMANDES SORTANTES EXISTANTES (nos demandes vers ce client) :
{json.dumps(outgoing_context, indent=2, ensure_ascii=False)}

DEMANDES ENTRANTES EXISTANTES (demandes de ce client vers nous) :
{json.dumps(incoming_context, indent=2, ensure_ascii=False)}

Analysez cet email et classifiez-le selon les catégories définies.
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
