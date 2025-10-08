-- Script SQL pour réinitialiser les connexions Outlook en ERROR
-- Usage : voir DATABASE_ACCESS_GUIDE.md

-- Réinitialiser TOUTES les connexions Outlook en ERROR vers ACTIVE
UPDATE email_connections 
SET 
    status = 'ACTIVE',
    consecutive_failures = 0,
    last_error = NULL
WHERE provider = 'OUTLOOK' 
  AND status = 'ERROR';

-- Afficher les connexions réinitialisées
SELECT 
    id,
    user_id,
    email_address,
    status,
    consecutive_failures,
    last_error,
    last_sync
FROM email_connections
WHERE provider = 'OUTLOOK';

