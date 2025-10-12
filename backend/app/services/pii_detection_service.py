"""
Service de détection et anonymisation des données sensibles (PII)
Utilise Microsoft Presidio pour une détection performante et gratuite
"""
from typing import Dict, Any, List, Optional
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
import hashlib
import json


class PIIDetectionService:
    """
    Service pour détecter et masquer les données sensibles (PII) dans les emails
    avant de les envoyer à l'IA pour classification
    
    Utilise les préférences de l'utilisateur pour déterminer quoi masquer
    """
    
    def __init__(self, db_session=None):
        """
        Initialise Presidio avec support multilingue (FR/EN)
        
        Args:
            db_session: Session SQLAlchemy pour charger les settings utilisateur
        """
        self.db = db_session
        
        try:
            # Configuration NLP avec spaCy
            configuration = {
                "nlp_engine_name": "spacy",
                "models": [
                    {"lang_code": "en", "model_name": "en_core_web_sm"},
                    {"lang_code": "fr", "model_name": "fr_core_news_sm"}
                ]
            }
            
            provider = NlpEngineProvider(nlp_configuration=configuration)
            nlp_engine = provider.create_engine()
            
            # Créer l'analyzer avec le moteur NLP
            self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
            self.anonymizer = AnonymizerEngine()
            
            # Types de PII à détecter (exhaustif)
            self.pii_entities = [
                "PERSON",           # Noms de personnes
                "EMAIL_ADDRESS",    # Emails
                "PHONE_NUMBER",     # Téléphones
                "CREDIT_CARD",      # Cartes bancaires
                "IBAN_CODE",        # IBAN
                "IP_ADDRESS",       # Adresses IP
                "LOCATION",         # Lieux/adresses
                "DATE_TIME",        # Dates (peuvent être sensibles)
                "NRP",              # Numéros nationaux (SSN, etc.)
                "MEDICAL_LICENSE",  # Licences médicales
                "URL",              # URLs (peuvent contenir tokens)
                "CRYPTO",           # Adresses crypto
                "US_SSN",           # SSN US
                "US_PASSPORT",      # Passeports
                "AU_ABN",           # ABN Australie
                "AU_ACN",           # ACN Australie
                "AU_TFN",           # TFN Australie
                "AU_MEDICARE",      # Medicare Australie
            ]
            
            print("✅ PII Detection Service initialized (Presidio + spaCy)")
            
        except Exception as e:
            print(f"⚠️ PII Detection Service initialization warning: {str(e)}")
            print("⚠️ Continuing without advanced PII detection (fallback to basic regex)")
            self.analyzer = None
            self.anonymizer = None
    
    def _get_user_settings(self, user_id: int):
        """Charge les settings PII de l'utilisateur depuis la DB"""
        if not self.db:
            return None
        
        from app.models.user_pii_settings import UserPIISettings, PIILevel
        settings = self.db.query(UserPIISettings).filter(
            UserPIISettings.user_id == user_id
        ).first()
        
        # Créer settings par défaut si n'existe pas
        if not settings:
            settings = UserPIISettings(
                user_id=user_id,
                protection_level=PIILevel.BASIC_REGEX
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        
        return settings
    
    def anonymize_email(
        self, 
        subject: str, 
        body: str, 
        sender_email: Optional[str] = None,
        sender_name: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Anonymise un email en masquant toutes les données sensibles
        SELON LES PRÉFÉRENCES DE L'UTILISATEUR
        
        Args:
            subject: Sujet de l'email
            body: Corps de l'email
            sender_email: Email de l'expéditeur (optionnel, sera masqué si fourni)
            sender_name: Nom de l'expéditeur (optionnel, sera masqué si fourni)
            user_id: ID utilisateur pour charger ses préférences
        
        Returns:
            dict avec:
                - anonymized_subject: Sujet anonymisé
                - anonymized_body: Corps anonymisé
                - anonymized_sender_name: Nom expéditeur anonymisé
                - pii_detected: Liste des PII détectées
                - pii_mapping: Mapping pour reverser l'anonymisation si besoin
        """
        
        # Charger les settings utilisateur
        from app.models.user_pii_settings import PIILevel
        settings = self._get_user_settings(user_id) if user_id else None
        
        # Si NONE → pas de masquage
        if settings and settings.protection_level == PIILevel.NONE:
            print(f"🔓 No PII masking (user preference)")
            return {
                "anonymized_subject": subject,
                "anonymized_body": body,
                "anonymized_sender_name": sender_name,
                "anonymized_sender_email": sender_email,
                "pii_detected": [],
                "pii_count": 0,
                "original_lengths": {"subject": len(subject), "body": len(body)}
            }
        
        # Si BASIC_REGEX ou pas de settings → regex basique
        if not settings or settings.protection_level == PIILevel.BASIC_REGEX:
            return self._basic_anonymization(subject, body, sender_name, settings)
        
        # Si ADVANCED_PRESIDIO et disponible → utiliser Presidio
        if settings.protection_level == PIILevel.ADVANCED_PRESIDIO and self.analyzer and self.anonymizer:
            return self._presidio_anonymization(subject, body, sender_name, sender_email, settings)
        
        # Fallback sur regex si Presidio indisponible
        if not self.analyzer or not self.anonymizer:
            print(f"⚠️ Presidio unavailable, falling back to regex")
            return self._basic_anonymization(subject, body, sender_name, settings)
        
    def _presidio_anonymization(self, subject: str, body: str, sender_name: Optional[str], sender_email: Optional[str], settings) -> Dict[str, Any]:
        """Anonymisation avancée avec Presidio"""
        try:
            # Déterminer quels entities utiliser
            entities_to_detect = self.pii_entities if not settings or not settings.enabled_entities else json.loads(settings.enabled_entities)
            
            # NOTE: Utiliser "en" car les recognizers Presidio ne supportent que l'anglais
            # Le modèle spaCy français sera quand même utilisé pour la NER (PERSON, LOCATION, etc.)
            
            # Analyser le sujet
            subject_results = self.analyzer.analyze(
                text=subject,
                language="en",  # Presidio recognizers supportent uniquement "en"
                entities=entities_to_detect
            )
            
            # Analyser le corps
            body_results = self.analyzer.analyze(
                text=body,
                language="en",
                entities=entities_to_detect
            )
            
            # Analyser le nom de l'expéditeur
            sender_name_results = []
            if sender_name:
                sender_name_results = self.analyzer.analyze(
                    text=sender_name,
                    language="en",
                    entities=entities_to_detect
                )
            
            # Anonymiser avec masquage par type
            # Créer un mapping pour chaque type d'entité
            operators = {}
            for entity_type in set([r.entity_type for r in subject_results + body_results + sender_name_results]):
                from presidio_anonymizer.entities import OperatorConfig
                operators[entity_type] = OperatorConfig("replace", {"new_value": f"<{entity_type}>"})
            
            anonymized_subject_result = self.anonymizer.anonymize(
                text=subject,
                analyzer_results=subject_results,
                operators=operators
            )
            
            anonymized_body_result = self.anonymizer.anonymize(
                text=body,
                analyzer_results=body_results,
                operators=operators
            )
            
            anonymized_sender_name = sender_name
            if sender_name and sender_name_results:
                anonymized_sender_name_result = self.anonymizer.anonymize(
                    text=sender_name,
                    analyzer_results=sender_name_results,
                    operators=operators
                )
                anonymized_sender_name = anonymized_sender_name_result.text
            
            # Masquer l'email de l'expéditeur (toujours)
            anonymized_sender_email = self._mask_email(sender_email) if sender_email else None
            
            # Compiler les PII détectées
            pii_detected = []
            for result in subject_results + body_results + sender_name_results:
                pii_detected.append({
                    "type": result.entity_type,
                    "score": result.score,
                    "start": result.start,
                    "end": result.end
                })
            
            return {
                "anonymized_subject": anonymized_subject_result.text,
                "anonymized_body": anonymized_body_result.text,
                "anonymized_sender_name": anonymized_sender_name,
                "anonymized_sender_email": anonymized_sender_email,
                "pii_detected": pii_detected,
                "pii_count": len(pii_detected),
                "original_lengths": {
                    "subject": len(subject),
                    "body": len(body)
                }
            }
            
        except Exception as e:
            print(f"⚠️ Presidio error: {str(e)}, falling back to regex")
            return self._basic_anonymization(subject, body, sender_name, settings)
    
    def _get_anonymization_operator(self):
        """
        Retourne l'opérateur d'anonymisation
        Masque par type (e.g., <PERSON>, <EMAIL>, <PHONE>)
        """
        from presidio_anonymizer.entities import OperatorConfig
        return OperatorConfig("replace", {"new_value": "<{entity_type}>"})
    
    def _mask_email(self, email: str) -> str:
        """Masque un email: melchior@example.com -> m***r@e***e.com"""
        if not email or '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        
        # Masquer la partie locale
        if len(local) <= 2:
            masked_local = local[0] + '*'
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        
        # Masquer le domaine
        if '.' in domain:
            domain_parts = domain.split('.')
            domain_name = domain_parts[0]
            if len(domain_name) <= 2:
                masked_domain = domain_name[0] + '*'
            else:
                masked_domain = domain_name[0] + '*' * (len(domain_name) - 2) + domain_name[-1]
            masked_domain += '.' + '.'.join(domain_parts[1:])
        else:
            masked_domain = domain[0] + '*' * (len(domain) - 1)
        
        return f"{masked_local}@{masked_domain}"
    
    def _basic_anonymization(self, subject: str, body: str, sender_name: Optional[str], settings=None) -> Dict[str, Any]:
        """
        Anonymisation basique avec regex enrichi (fallback si Presidio indisponible)
        Détecte: emails, téléphones, IBAN, cartes bancaires, URLs, IPs, numéros divers
        Respecte les préférences utilisateur si settings fourni
        """
        import re
        
        # Patterns regex enrichis
        all_patterns = {
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'PHONE': r'(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}[-.\s]?\d{0,4}',
            'IBAN': r'\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b',
            'CREDIT_CARD': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'URL': r'https?://[^\s<>"{}|\\^`\[\]]+',
            'IP_ADDRESS': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'SSN_US': r'\b\d{3}-\d{2}-\d{4}\b',
            'POSTAL_CODE_CH': r'\b\d{4}\b',  # Code postal suisse
            'DATE': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        }
        
        # Filtrer les patterns selon les settings utilisateur
        patterns = {}
        if settings:
            if settings.mask_emails:
                patterns['EMAIL'] = all_patterns['EMAIL']
            if settings.mask_phones:
                patterns['PHONE'] = all_patterns['PHONE']
            if settings.mask_iban:
                patterns['IBAN'] = all_patterns['IBAN']
            if settings.mask_credit_cards:
                patterns['CREDIT_CARD'] = all_patterns['CREDIT_CARD']
            if settings.mask_urls:
                patterns['URL'] = all_patterns['URL']
            if settings.mask_ip_addresses:
                patterns['IP_ADDRESS'] = all_patterns['IP_ADDRESS']
            if settings.mask_dates:
                patterns['DATE'] = all_patterns['DATE']
        else:
            # Par défaut, tout sauf URLs, IPs et dates
            patterns = {k: v for k, v in all_patterns.items() if k not in ['URL', 'IP_ADDRESS', 'DATE']}
        
        anonymized_subject = subject
        anonymized_body = body
        pii_count = 0
        pii_details = []
        
        # Appliquer chaque pattern
        for pii_type, pattern in patterns.items():
            # Masquer dans le corps
            matches = re.findall(pattern, anonymized_body)
            for match in matches:
                match_str = match if isinstance(match, str) else match[0] if isinstance(match, tuple) else str(match)
                
                # Filtres pour éviter faux positifs
                if pii_type == 'PHONE' and len(match_str.replace(' ', '').replace('-', '')) < 8:
                    continue
                if pii_type == 'IP_ADDRESS' and not all(0 <= int(x) <= 255 for x in match_str.split('.')):
                    continue
                if pii_type == 'POSTAL_CODE_CH' and match_str in ['1000', '2000', '9999']:  # Codes génériques
                    continue
                
                anonymized_body = anonymized_body.replace(match_str, f'<{pii_type}>')
                pii_count += 1
                pii_details.append({"type": pii_type, "length": len(match_str)})
            
            # Masquer aussi dans le sujet (sauf URLs et IPs)
            if pii_type not in ['URL', 'IP_ADDRESS', 'DATE']:
                matches_subject = re.findall(pattern, anonymized_subject)
                for match in matches_subject:
                    match_str = match if isinstance(match, str) else match[0] if isinstance(match, tuple) else str(match)
                    anonymized_subject = anonymized_subject.replace(match_str, f'<{pii_type}>')
                    pii_count += 1
        
        return {
            "anonymized_subject": anonymized_subject,
            "anonymized_body": anonymized_body,
            "anonymized_sender_name": sender_name,
            "anonymized_sender_email": None,
            "pii_detected": pii_details,
            "pii_count": pii_count,
            "original_lengths": {
                "subject": len(subject),
                "body": len(body)
            }
        }
    
    def should_anonymize_for_client(self, client_id: Optional[int]) -> bool:
        """
        Détermine si on doit anonymiser pour ce client
        Pour l'instant, toujours anonymiser si un client est matché
        """
        return client_id is not None

