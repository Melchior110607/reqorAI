-- Add reminder and follow-up features for requests

-- 1. Reminder configuration for outgoing requests
ALTER TABLE requests ADD COLUMN IF NOT EXISTS reminder_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE requests ADD COLUMN IF NOT EXISTS reminder_frequency VARCHAR(20); -- 'daily', 'weekly', 'biweekly', 'monthly'
ALTER TABLE requests ADD COLUMN IF NOT EXISTS reminder_message TEXT; -- Custom or AI-generated reminder
ALTER TABLE requests ADD COLUMN IF NOT EXISTS last_reminder_sent_at TIMESTAMPTZ;
ALTER TABLE requests ADD COLUMN IF NOT EXISTS reminder_count INTEGER DEFAULT 0;

-- 2. Follow-up tracking for incoming requests
ALTER TABLE requests ADD COLUMN IF NOT EXISTS is_follow_up BOOLEAN DEFAULT FALSE; -- Is this a follow-up to another request?
ALTER TABLE requests ADD COLUMN IF NOT EXISTS parent_request_id INTEGER REFERENCES requests(id) ON DELETE SET NULL; -- Original request
ALTER TABLE requests ADD COLUMN IF NOT EXISTS follow_up_type VARCHAR(50); -- 'client_reminder', 'dissatisfaction', null
ALTER TABLE requests ADD COLUMN IF NOT EXISTS follow_up_count INTEGER DEFAULT 0; -- Number of times client followed up

-- 3. Add index for efficient queries
CREATE INDEX IF NOT EXISTS idx_requests_reminder_enabled ON requests(reminder_enabled, status) WHERE reminder_enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_requests_parent_request ON requests(parent_request_id) WHERE parent_request_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_requests_follow_up_type ON requests(follow_up_type);

-- 4. Update existing incoming requests to track conversation threads
ALTER TABLE intercepted_emails ADD COLUMN IF NOT EXISTS conversation_thread_id VARCHAR(500); -- Gmail/Outlook thread ID
ALTER TABLE intercepted_emails ADD COLUMN IF NOT EXISTS in_reply_to_message_id VARCHAR(500); -- Original message being replied to

CREATE INDEX IF NOT EXISTS idx_intercepted_emails_thread ON intercepted_emails(conversation_thread_id);
CREATE INDEX IF NOT EXISTS idx_intercepted_emails_reply_to ON intercepted_emails(in_reply_to_message_id);

COMMENT ON COLUMN requests.reminder_enabled IS 'Enable automatic reminders for outgoing requests';
COMMENT ON COLUMN requests.follow_up_type IS 'Type: client_reminder (same request again) or dissatisfaction (wants more)';

