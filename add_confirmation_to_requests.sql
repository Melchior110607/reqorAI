-- Migration : Ajouter les colonnes de confirmation aux requests
-- Date : 2025-10-08
-- Description : Ajout de confirmation_received, confirmation_received_at et confirmation_details pour tracking

-- Ajouter la colonne confirmation_received
ALTER TABLE requests 
ADD COLUMN IF NOT EXISTS confirmation_received BOOLEAN DEFAULT FALSE;

-- Ajouter la colonne confirmation_received_at
ALTER TABLE requests 
ADD COLUMN IF NOT EXISTS confirmation_received_at TIMESTAMP WITH TIME ZONE;

-- Ajouter la colonne confirmation_details
ALTER TABLE requests 
ADD COLUMN IF NOT EXISTS confirmation_details TEXT;

-- Afficher la structure de la table pour confirmation
\d requests



