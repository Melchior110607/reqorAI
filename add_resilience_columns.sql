-- Migration : Ajouter les colonnes de résilience à email_connections
-- Date : 2025-10-08
-- Description : Ajout de consecutive_failures et last_error pour gestion d'erreur robuste

-- Ajouter la colonne consecutive_failures
ALTER TABLE email_connections 
ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER DEFAULT 0;

-- Ajouter la colonne last_error
ALTER TABLE email_connections 
ADD COLUMN IF NOT EXISTS last_error TEXT;

-- Afficher la structure de la table pour confirmation
\d email_connections

