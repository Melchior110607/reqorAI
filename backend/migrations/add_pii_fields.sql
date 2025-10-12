-- Migration: Ajout des champs pour la protection des données sensibles (PII)

-- Ajouter les colonnes pour stocker les versions anonymisées
ALTER TABLE intercepted_emails 
ADD COLUMN IF NOT EXISTS anonymized_subject TEXT,
ADD COLUMN IF NOT EXISTS anonymized_body TEXT,
ADD COLUMN IF NOT EXISTS anonymized_sender_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS pii_detected_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS pii_detection_metadata TEXT; -- JSON avec détails PII détectées

-- Créer un index pour rechercher rapidement les emails avec PII détectées
CREATE INDEX IF NOT EXISTS idx_intercepted_emails_pii_count 
ON intercepted_emails(pii_detected_count) WHERE pii_detected_count > 0;

COMMENT ON COLUMN intercepted_emails.anonymized_subject IS 'Sujet de l''email avec données sensibles masquées (envoyé à l''IA)';
COMMENT ON COLUMN intercepted_emails.anonymized_body IS 'Corps de l''email avec données sensibles masquées (envoyé à l''IA)';
COMMENT ON COLUMN intercepted_emails.anonymized_sender_name IS 'Nom expéditeur avec données sensibles masquées';
COMMENT ON COLUMN intercepted_emails.pii_detected_count IS 'Nombre de PII détectées dans l''email';
COMMENT ON COLUMN intercepted_emails.pii_detection_metadata IS 'Métadonnées JSON sur les PII détectées (types, scores, etc.)';

