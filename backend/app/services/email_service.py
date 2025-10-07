import json
import re
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from fuzzywuzzy import fuzz
from app.models.client import Client
from app.models.client_email_rule import ClientEmailRule, RuleType
from app.models.intercepted_email import InterceptedEmail, ProcessingStatus
from app.models.email_connection import EmailConnection

class EmailMatchingService:
    def __init__(self, db: Session):
        self.db = db

    def find_matching_client(self, sender_email: str, user_id: int) -> Tuple[Optional[Client], float, Optional[ClientEmailRule]]:
        """
        Trouve le client correspondant à un email avec score de confiance
        Returns: (client, confidence_score, matched_rule)
        """
        sender_email = sender_email.lower().strip()
        domain = sender_email.split('@')[-1] if '@' in sender_email else ''
        
        # Récupérer tous les clients et leurs règles pour cet utilisateur
        clients_with_rules = self.db.query(Client).filter(Client.user_id == user_id).all()
        
        best_match = None
        best_score = 0.0
        best_rule = None
        
        for client in clients_with_rules:
            # Vérifier les règles explicites d'abord
            for rule in client.email_rules:
                if not rule.is_active:
                    continue
                    
                score = self._evaluate_rule(sender_email, domain, rule)
                if score > best_score:
                    best_match = client
                    best_score = score
                    best_rule = rule
            
            # Si pas de règles explicites, utiliser la correspondance automatique
            if not client.email_rules:
                score = self._auto_match_client(sender_email, domain, client)
                if score > best_score:
                    best_match = client
                    best_score = score
                    best_rule = None
        
        return best_match, best_score, best_rule

    def _evaluate_rule(self, sender_email: str, domain: str, rule: ClientEmailRule) -> float:
        """Évalue une règle spécifique"""
        pattern = rule.pattern.lower()
        
        if rule.rule_type == RuleType.EXACT:
            return rule.confidence_score if sender_email == pattern else 0.0
        
        elif rule.rule_type == RuleType.DOMAIN:
            return rule.confidence_score if domain == pattern else 0.0
        
        elif rule.rule_type == RuleType.SUBDOMAIN:
            # Pattern: amazon.com matches *.amazon.com
            if domain.endswith(pattern) or domain == pattern:
                return rule.confidence_score
            return 0.0
        
        elif rule.rule_type == RuleType.CONTAINS:
            if pattern in sender_email:
                return rule.confidence_score
            return 0.0
        
        return 0.0

    def _auto_match_client(self, sender_email: str, domain: str, client: Client) -> float:
        """Correspondance automatique basée sur le nom de l'entreprise"""
        company_name = client.company.lower()
        client_email = client.email.lower()
        
        # Correspondance exacte d'email
        if sender_email == client_email:
            return 1.0
        
        # Correspondance de domaine
        client_domain = client_email.split('@')[-1] if '@' in client_email else ''
        if domain == client_domain:
            return 0.9
        
        # Correspondance fuzzy du nom d'entreprise dans l'email
        company_words = company_name.split()
        max_similarity = 0.0
        
        for word in company_words:
            if len(word) > 3:  # Ignorer les mots trop courts
                if word in sender_email:
                    max_similarity = max(max_similarity, 0.8)
                elif word in domain:
                    max_similarity = max(max_similarity, 0.7)
                else:
                    # Fuzzy matching
                    email_similarity = fuzz.partial_ratio(word, sender_email) / 100.0
                    domain_similarity = fuzz.partial_ratio(word, domain) / 100.0
                    max_similarity = max(max_similarity, email_similarity * 0.6, domain_similarity * 0.5)
        
        return max_similarity if max_similarity > 0.6 else 0.0

    def create_email_rules_for_client(self, client_id: int, email_address: str) -> List[ClientEmailRule]:
        """Crée automatiquement des règles d'email pour un client"""
        domain = email_address.split('@')[-1] if '@' in email_address else ''
        
        rules = []
        
        # Règle de domaine exact
        if domain:
            domain_rule = ClientEmailRule(
                client_id=client_id,
                rule_type=RuleType.DOMAIN,
                pattern=domain,
                confidence_score=0.9
            )
            rules.append(domain_rule)
        
        # Règle d'email exact
        exact_rule = ClientEmailRule(
            client_id=client_id,
            rule_type=RuleType.EXACT,
            pattern=email_address.lower(),
            confidence_score=1.0
        )
        rules.append(exact_rule)
        
        return rules

class EmailProcessingService:
    def __init__(self, db: Session):
        self.db = db
        self.matching_service = EmailMatchingService(db)

    def process_intercepted_email(self, email_data: dict, connection_id: int, user_id: int) -> Optional[InterceptedEmail]:
        """Traite un email intercepté (retourne None si doublon)"""
        message_id = email_data.get('id')
        if not message_id:
            print("⚠️ Email sans message_id, ignoré")
            return None
        
        # ANTI-DOUBLON: Vérifier si cet email existe déjà
        existing = self.db.query(InterceptedEmail).filter(
            InterceptedEmail.message_id == message_id
        ).first()
        
        if existing:
            print(f"🔄 Email {message_id} déjà traité, ignoré")
            return None
        
        sender_email = email_data.get('sender_email', '').lower()
        
        # Trouver le client correspondant
        client, confidence, rule = self.matching_service.find_matching_client(sender_email, user_id)
        
        # Créer l'enregistrement d'email intercepté
        intercepted_email = InterceptedEmail(
            user_id=user_id,
            connection_id=connection_id,
            client_id=client.id if client else None,
            message_id=message_id,
            sender_email=sender_email,
            sender_name=email_data.get('sender_name', ''),
            subject=email_data.get('subject', ''),
            body=email_data.get('body', ''),
            attachments=json.dumps(email_data.get('attachments', [])),
            email_thread_id=email_data.get('thread_id'),
            confidence_score=confidence,
            matched_rule_id=rule.id if rule else None,
            email_received_at=email_data.get('received_at'),
            processing_status=ProcessingStatus.PENDING
        )
        
        self.db.add(intercepted_email)
        self.db.commit()
        self.db.refresh(intercepted_email)
        
        return intercepted_email
