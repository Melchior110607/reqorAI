from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

# Configuration
configuration = {
    'nlp_engine_name': 'spacy',
    'models': [
        {'lang_code': 'en', 'model_name': 'en_core_web_sm'},
        {'lang_code': 'fr', 'model_name': 'fr_core_news_sm'}
    ]
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()
analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

# Test texte
text = """
Bonjour, je m'appelle Jean Dupont.
Email: jean.dupont@test.ch
Téléphone: +41 78 123 45 67
"""

print("Test 1: Sans entities")
try:
    results = analyzer.analyze(text=text, language="fr")
    print(f"✅ {len(results)} entités détectées")
    for r in results:
        print(f"   - {r.entity_type} (score: {r.score:.2f})")
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\nTest 2: Avec entities list")
try:
    entities = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"]
    results = analyzer.analyze(text=text, language="fr", entities=entities)
    print(f"✅ {len(results)} entités détectées")
    for r in results:
        print(f"   - {r.entity_type} (score: {r.score:.2f})")
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\nTest 3: Liste complète")
try:
    entities = [
        "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "CREDIT_CARD", "IBAN_CODE",
        "IP_ADDRESS", "LOCATION", "DATE_TIME", "NRP", "MEDICAL_LICENSE",
        "URL", "CRYPTO", "US_SSN", "US_PASSPORT", "AU_ABN", "AU_ACN",
        "AU_TFN", "AU_MEDICARE"
    ]
    results = analyzer.analyze(text=text, language="fr", entities=entities)
    print(f"✅ {len(results)} entités détectées")
    for r in results:
        print(f"   - {r.entity_type} (score: {r.score:.2f})")
except Exception as e:
    print(f"❌ Erreur: {e}")
