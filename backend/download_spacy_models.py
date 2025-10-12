#!/usr/bin/env python3
"""
Script pour télécharger les modèles spaCy nécessaires pour la détection PII
Exécuté au build du conteneur Docker
"""
import subprocess
import sys

def download_models():
    """Télécharge les modèles spaCy pour FR et EN"""
    models = [
        ("en_core_web_sm", "English"),
        ("fr_core_news_sm", "French")
    ]
    
    for model_name, language in models:
        print(f"📥 Downloading {language} model: {model_name}...")
        try:
            # Use pip install instead of spacy download (more reliable in Docker)
            subprocess.run(
                [sys.executable, "-m", "pip", "install", f"https://github.com/explosion/spacy-models/releases/download/{model_name}-3.7.1/{model_name}-3.7.1-py3-none-any.whl"],
                check=True
            )
            print(f"✅ {language} model downloaded successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Failed to download {language} model: {e}")
            print(f"   Continuing anyway - PII detection will fall back to basic regex")
    
    print("\n✅ All spaCy models downloaded!")

if __name__ == "__main__":
    download_models()

