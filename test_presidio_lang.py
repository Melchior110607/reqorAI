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

# Test texte (en français mais on va tester avec différentes langues)
text = """
Hello, my name is Jean Dupont.
Email: jean.dupont@test.ch
Phone: +41 78 123 45 67
"""

print("=" * 60)
print("Test avec language='en'")
print("=" * 60)
try:
    results = analyzer.analyze(text=text, language="en")
    print(f"✅ {len(results)} entités détectées")
    for r in results:
        print(f"   - {r.entity_type} at [{r.start}:{r.end}] = '{text[r.start:r.end]}' (score: {r.score:.2f})")
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n" + "=" * 60)
print("Test avec language='fr'")
print("=" * 60)
try:
    results = analyzer.analyze(text=text, language="fr")
    print(f"✅ {len(results)} entités détectées")
    for r in results:
        print(f"   - {r.entity_type} at [{r.start}:{r.end}] = '{text[r.start:r.end]}' (score: {r.score:.2f})")
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n" + "=" * 60)
print("Vérification: Quels recognizers supportent 'fr' ?")
print("=" * 60)
for recognizer in analyzer.registry.recognizers:
    langs = recognizer.supported_language
    if 'fr' in langs or 'all' in langs:
        print(f"✅ {recognizer.name}: {recognizer.supported_entities}")
    else:
        print(f"❌ {recognizer.name}: {recognizer.supported_entities} (only {langs})")
