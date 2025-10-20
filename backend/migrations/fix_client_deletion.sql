-- Fix foreign key constraint for client deletion
-- Allow intercepted_emails.client_id to be set to NULL when client is deleted

-- Drop existing constraint
ALTER TABLE intercepted_emails DROP CONSTRAINT IF EXISTS intercepted_emails_client_id_fkey;

-- Re-add with ON DELETE SET NULL
ALTER TABLE intercepted_emails 
ADD CONSTRAINT intercepted_emails_client_id_fkey 
FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE SET NULL;

-- Also fix for matched_rule_id
ALTER TABLE intercepted_emails DROP CONSTRAINT IF EXISTS intercepted_emails_matched_rule_id_fkey;

ALTER TABLE intercepted_emails 
ADD CONSTRAINT intercepted_emails_matched_rule_id_fkey 
FOREIGN KEY (matched_rule_id) REFERENCES client_email_rules(id) ON DELETE SET NULL;

