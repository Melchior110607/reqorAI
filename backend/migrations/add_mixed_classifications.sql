-- Migration: Add support for MIXED email classifications
-- Date: 2025-10-19

-- Add ai_sub_classifications column to intercepted_emails
ALTER TABLE intercepted_emails 
ADD COLUMN IF NOT EXISTS ai_sub_classifications TEXT;

-- Comment
COMMENT ON COLUMN intercepted_emails.ai_sub_classifications IS 'JSON array of sub-classifications for MIXED emails: [{"classification": "new_request", "request_ids": [1,2]}, ...]';

