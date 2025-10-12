"""
Test complet de l'algorithme de détection PII
"""
import sys
sys.path.insert(0, '/app')

from app.services.pii_detection_service import PIIDetectionService
from app.database.config import get_db
from app.models.user_pii_settings import UserPIISettings, PIILevel

# Email de test réaliste
test_email = {
    "subject": "Demande de devis pour projet web",
    "body": """
Bonjour,

Je me permets de vous contacter pour un projet de développement web.

Voici mes coordonnées:
- Email: jean.dupont@entreprise-test.ch
- Téléphone: +41 78 123 45 67
- IBAN: CH93 0076 2011 6238 5295 7
- Carte: 4532 1234 5678 9010

Notre siège est situé au Chemin des Acacias 12, 1227 Genève.

Pourriez-vous me faire parvenir un devis pour début mars 2025?

Site web: https://www.entreprise-test.ch
IP du serveur actuel: 192.168.1.100

Cordialement,
Jean Dupont
Directeur Technique
    """,
    "sender_name": "Jean Dupont",
    "sender_email": "jean.dupont@entreprise-test.ch"
}

print("=" * 80)
print("🧪 TEST COMPLET - DÉTECTION PII")
print("=" * 80)

# Créer une session DB
db = next(get_db())

# Initialiser le service PII
pii_service = PIIDetectionService(db_session=db)

print("\n📧 EMAIL DE TEST:")
print(f"Subject: {test_email['subject']}")
print(f"From: {test_email['sender_name']} <{test_email['sender_email']}>")
print(f"Body length: {len(test_email['body'])} chars")

# Test 1: NONE (pas de masquage)
print("\n" + "=" * 80)
print("TEST 1: Protection Level = NONE")
print("=" * 80)

# Créer/mettre à jour les settings utilisateur
settings = db.query(UserPIISettings).filter(UserPIISettings.user_id == 3).first()
if settings:
    settings.protection_level = PIILevel.NONE
    db.commit()

result_none = pii_service.anonymize_email(
    subject=test_email['subject'],
    body=test_email['body'],
    sender_name=test_email['sender_name'],
    sender_email=test_email['sender_email'],
    user_id=3
)

print(f"\n✅ PII détectées: {result_none['pii_count']}")
print(f"📝 Subject: {result_none['anonymized_subject']}")
print(f"📝 Body (first 200 chars): {result_none['anonymized_body'][:200]}...")
print(f"👤 Sender: {result_none['anonymized_sender_name']}")

# Test 2: BASIC_REGEX
print("\n" + "=" * 80)
print("TEST 2: Protection Level = BASIC_REGEX")
print("=" * 80)

if settings:
    settings.protection_level = PIILevel.BASIC_REGEX
    db.commit()

result_basic = pii_service.anonymize_email(
    subject=test_email['subject'],
    body=test_email['body'],
    sender_name=test_email['sender_name'],
    sender_email=test_email['sender_email'],
    user_id=3
)

print(f"\n✅ PII détectées: {result_basic['pii_count']}")
print(f"📊 Types détectés: {[p['type'] for p in result_basic.get('pii_detected', [])]}")
print(f"\n📝 Subject anonymisé: {result_basic['anonymized_subject']}")
print(f"\n📝 Body anonymisé:")
print(result_basic['anonymized_body'])
print(f"\n👤 Sender anonymisé: {result_basic['anonymized_sender_name']}")

# Test 3: ADVANCED_PRESIDIO
print("\n" + "=" * 80)
print("TEST 3: Protection Level = ADVANCED_PRESIDIO")
print("=" * 80)

if settings:
    settings.protection_level = PIILevel.ADVANCED_PRESIDIO
    db.commit()

result_advanced = pii_service.anonymize_email(
    subject=test_email['subject'],
    body=test_email['body'],
    sender_name=test_email['sender_name'],
    sender_email=test_email['sender_email'],
    user_id=3
)

print(f"\n✅ PII détectées: {result_advanced['pii_count']}")
print(f"📊 Types détectés: {[p['type'] for p in result_advanced.get('pii_detected', [])]}")
print(f"\n📝 Body anonymisé:")
print(result_advanced['anonymized_body'])

# Comparaison
print("\n" + "=" * 80)
print("📊 COMPARAISON DES RÉSULTATS")
print("=" * 80)
print(f"NONE:              {result_none['pii_count']} PII détectées")
print(f"BASIC_REGEX:       {result_basic['pii_count']} PII détectées")
print(f"ADVANCED_PRESIDIO: {result_advanced['pii_count']} PII détectées")

print("\n✅ Test terminé!")
