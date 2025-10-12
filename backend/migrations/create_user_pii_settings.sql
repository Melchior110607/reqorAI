-- Migration: Créer la table user_pii_settings pour la configuration de confidentialité

-- Créer le type enum pour les niveaux de protection
CREATE TYPE pii_level AS ENUM ('none', 'basic_regex', 'advanced_presidio', 'custom');

-- Créer la table
CREATE TABLE IF NOT EXISTS user_pii_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    
    -- Niveau de protection
    protection_level pii_level NOT NULL DEFAULT 'basic_regex',
    
    -- Configuration personnalisée
    enabled_entities TEXT,  -- JSON array
    
    -- Options individuelles
    mask_emails BOOLEAN DEFAULT TRUE,
    mask_phones BOOLEAN DEFAULT TRUE,
    mask_persons BOOLEAN DEFAULT FALSE,
    mask_locations BOOLEAN DEFAULT FALSE,
    mask_dates BOOLEAN DEFAULT FALSE,
    mask_credit_cards BOOLEAN DEFAULT TRUE,
    mask_iban BOOLEAN DEFAULT TRUE,
    mask_urls BOOLEAN DEFAULT FALSE,
    mask_ip_addresses BOOLEAN DEFAULT FALSE,
    
    -- Avertissement accepté
    context_warning_acknowledged BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index
CREATE INDEX idx_user_pii_settings_user_id ON user_pii_settings(user_id);

-- Commentaires
COMMENT ON TABLE user_pii_settings IS 'Configuration de la protection des données sensibles (PII) par utilisateur';
COMMENT ON COLUMN user_pii_settings.protection_level IS 'Niveau de protection: none, basic_regex, advanced_presidio, custom';
COMMENT ON COLUMN user_pii_settings.enabled_entities IS 'Liste JSON des types de PII à masquer (pour mode custom)';
COMMENT ON COLUMN user_pii_settings.context_warning_acknowledged IS 'L''utilisateur a compris que moins de masquage = meilleur contexte IA';

