-- Add follow-up message fields to requests table

ALTER TABLE requests ADD COLUMN IF NOT EXISTS latest_follow_up_message TEXT;
ALTER TABLE requests ADD COLUMN IF NOT EXISTS latest_follow_up_at TIMESTAMPTZ;

COMMENT ON COLUMN requests.latest_follow_up_message IS 'Latest client follow-up message (reminder or dissatisfaction)';
COMMENT ON COLUMN requests.latest_follow_up_at IS 'Timestamp of the latest follow-up received';

