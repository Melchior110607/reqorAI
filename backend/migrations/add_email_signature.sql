-- Add email signature to users table

ALTER TABLE users ADD COLUMN IF NOT EXISTS email_signature TEXT;

COMMENT ON COLUMN users.email_signature IS 'User email signature for AI-generated emails';

