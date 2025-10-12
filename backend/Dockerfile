FROM python:3.11-slim

WORKDIR /app

# Installer les dépendances système pour spaCy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Installer les packages Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Télécharger les modèles spaCy pour la détection PII
RUN python download_spacy_models.py || echo "⚠️ spaCy models download failed, will use fallback"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
