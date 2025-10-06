"""
Script pour insérer des données de test pour le debugging de l'algorithme email
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database.config import SessionLocal

# Import dans le bon ordre pour éviter les dépendances circulaires
from app.models.user import User, AuthProvider
from app.models.client import Client
from app.models.request import Request  # Important pour résoudre les relations
from app.models.email_connection import EmailConnection, EmailProvider, ConnectionStatus
from app.models.client_email_rule import ClientEmailRule, RuleType
from app.models.intercepted_email import InterceptedEmail, EmailClassification, ProcessingStatus

def create_test_data():
    db = SessionLocal()
    
    try:
        print("🔍 Création des données de test...")
        
        # 1. Trouver ou créer un utilisateur de test
        test_user = db.query(User).filter(User.email.like('%gmail.com')).first()
        if not test_user:
            print("❌ Aucun utilisateur trouvé. Connectez-vous d'abord avec Google OAuth.")
            return
        
        print(f"✓ Utilisateur trouvé: {test_user.email}")
        
        # 2. Créer une connexion email si elle n'existe pas
        email_conn = db.query(EmailConnection).filter(
            EmailConnection.user_id == test_user.id
        ).first()
        
        if not email_conn:
            email_conn = EmailConnection(
                user_id=test_user.id,
                provider=EmailProvider.GMAIL,
                email_address=test_user.email,
                access_token="test_token",
                status=ConnectionStatus.ACTIVE
            )
            db.add(email_conn)
            db.commit()
            db.refresh(email_conn)
            print(f"✓ Connexion email créée: {email_conn.email_address}")
        else:
            print(f"✓ Connexion email existante: {email_conn.email_address}")
        
        # 3. Créer des clients de test avec règles
        clients_data = [
            {
                "name": "Amazon",
                "company": "Amazon Inc",
                "email": "contact@amazon.com",
                "rules": [
                    {"type": RuleType.DOMAIN, "pattern": "amazon.com"},
                    {"type": RuleType.CONTAINS, "pattern": "amazon"}
                ]
            },
            {
                "name": "Google",
                "company": "Google LLC",
                "email": "contact@google.com",
                "rules": [
                    {"type": RuleType.DOMAIN, "pattern": "google.com"},
                    {"type": RuleType.SUBDOMAIN, "pattern": "google.com"}
                ]
            },
            {
                "name": "Microsoft",
                "company": "Microsoft Corporation",
                "email": "contact@microsoft.com",
                "rules": [
                    {"type": RuleType.DOMAIN, "pattern": "microsoft.com"},
                    {"type": RuleType.CONTAINS, "pattern": "microsoft"}
                ]
            }
        ]
        
        for client_data in clients_data:
            # Vérifier si le client existe déjà
            existing_client = db.query(Client).filter(
                Client.user_id == test_user.id,
                Client.name == client_data["name"]
            ).first()
            
            if not existing_client:
                client = Client(
                    user_id=test_user.id,
                    name=client_data["name"],
                    company=client_data["company"],
                    email=client_data["email"]
                )
                db.add(client)
                db.commit()
                db.refresh(client)
                print(f"✓ Client créé: {client.name}")
                
                # Créer les règles
                for rule_data in client_data["rules"]:
                    rule = ClientEmailRule(
                        client_id=client.id,
                        rule_type=rule_data["type"],
                        pattern=rule_data["pattern"],
                        confidence_score=0.9,
                        is_active=True
                    )
                    db.add(rule)
                
                db.commit()
                print(f"  → {len(client_data['rules'])} règles créées")
            else:
                client = existing_client
                print(f"✓ Client existant: {client.name}")
        
        # 4. Créer des emails interceptés de test
        test_emails = [
            {
                "sender": "john.doe@amazon.com",
                "name": "John Doe",
                "subject": "Re: Product inquiry",
                "body": "Thank you for your inquiry about our products. We'd be happy to help you with more information.",
                "should_match": "Amazon"
            },
            {
                "sender": "support@google.com",
                "name": "Google Support",
                "subject": "Your account verification",
                "body": "Please verify your account by clicking the link below.",
                "should_match": "Google"
            },
            {
                "sender": "noreply@service.microsoft.com",
                "name": "Microsoft Services",
                "subject": "License renewal reminder",
                "body": "Your Microsoft 365 license will expire soon. Please renew to continue using our services.",
                "should_match": "Microsoft"
            },
            {
                "sender": "info@randomcompany.com",
                "name": "Random Company",
                "subject": "Partnership opportunity",
                "body": "We would like to discuss a potential partnership with your company.",
                "should_match": None
            },
            {
                "sender": "sales@amazon-marketplace.com",
                "name": "Amazon Marketplace",
                "subject": "New seller application",
                "body": "Your application to become a seller on Amazon Marketplace has been received.",
                "should_match": "Amazon"  # Devrait matcher via "contains"
            }
        ]
        
        for email_data in test_emails:
            # Trouver le client correspondant
            client_id = None
            matched_rule_id = None
            confidence = 0.0
            
            if email_data["should_match"]:
                client = db.query(Client).filter(
                    Client.user_id == test_user.id,
                    Client.name == email_data["should_match"]
                ).first()
                
                if client:
                    # Trouver une règle qui matche
                    rules = db.query(ClientEmailRule).filter(
                        ClientEmailRule.client_id == client.id,
                        ClientEmailRule.is_active == True
                    ).all()
                    
                    for rule in rules:
                        if rule.rule_type == RuleType.DOMAIN:
                            if email_data["sender"].endswith(f"@{rule.pattern}"):
                                client_id = client.id
                                matched_rule_id = rule.id
                                confidence = rule.confidence_score
                                break
                        elif rule.rule_type == RuleType.CONTAINS:
                            if rule.pattern.lower() in email_data["sender"].lower():
                                client_id = client.id
                                matched_rule_id = rule.id
                                confidence = rule.confidence_score * 0.8  # Moins de confiance pour "contains"
                                break
            
            # Vérifier si l'email existe déjà
            existing_email = db.query(InterceptedEmail).filter(
                InterceptedEmail.sender_email == email_data["sender"],
                InterceptedEmail.subject == email_data["subject"]
            ).first()
            
            if not existing_email:
                intercepted_email = InterceptedEmail(
                    user_id=test_user.id,
                    connection_id=email_conn.id,
                    client_id=client_id,
                    sender_email=email_data["sender"],
                    sender_name=email_data["name"],
                    subject=email_data["subject"],
                    body=email_data["body"],
                    confidence_score=confidence,
                    matched_rule_id=matched_rule_id,
                    ai_classification=EmailClassification.UNCLASSIFIED,
                    ai_confidence=0.0,
                    processing_status=ProcessingStatus.PENDING,
                    email_received_at=datetime.now() - timedelta(hours=len(test_emails) - test_emails.index(email_data))
                )
                db.add(intercepted_email)
                match_status = f"✓ Match: {email_data['should_match']}" if client_id else "✗ No match"
                print(f"✓ Email créé: {email_data['sender']} → {match_status}")
            else:
                print(f"✓ Email existant: {email_data['sender']}")
        
        db.commit()
        
        # 5. Afficher les statistiques
        print("\n📊 Statistiques:")
        total_clients = db.query(Client).filter(Client.user_id == test_user.id).count()
        total_rules = db.query(ClientEmailRule).join(Client).filter(Client.user_id == test_user.id).count()
        total_emails = db.query(InterceptedEmail).filter(InterceptedEmail.user_id == test_user.id).count()
        matched_emails = db.query(InterceptedEmail).filter(
            InterceptedEmail.user_id == test_user.id,
            InterceptedEmail.client_id.isnot(None)
        ).count()
        
        print(f"  Clients: {total_clients}")
        print(f"  Règles: {total_rules}")
        print(f"  Emails: {total_emails}")
        print(f"  Matched: {matched_emails}")
        print(f"  Unmatched: {total_emails - matched_emails}")
        
        print("\n✅ Données de test créées avec succès!")
        print("\n🔗 Accédez à http://localhost:3000/ai-monitoring pour voir les résultats")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data()

