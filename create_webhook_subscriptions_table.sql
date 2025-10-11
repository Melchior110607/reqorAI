-- Migration: Create webhook_subscriptions table
-- This table tracks webhook subscriptions for both Gmail and Outlook

CREATE TABLE IF NOT EXISTS webhook_subscriptions (
    id SERIAL PRIMARY KEY,
    connection_id INTEGER NOT NULL REFERENCES email_connections(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- 'GMAIL' or 'OUTLOOK'
    
    -- Gmail specific (Pub/Sub)
    topic_name VARCHAR(500),  -- e.g., 'projects/xxx/topics/gmail-notifications'
    history_id BIGINT,  -- Gmail history ID to track changes
    
    -- Outlook specific (Microsoft Graph)
    subscription_id VARCHAR(500),  -- Microsoft Graph subscription ID
    resource VARCHAR(500),  -- Resource path (e.g., '/me/mailFolders/inbox/messages')
    client_state VARCHAR(255),  -- Secret token for validation
    
    -- Common fields
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',  -- 'active', 'expired', 'failed', 'renewing'
    last_notification_at TIMESTAMP WITH TIME ZONE,
    notification_count INTEGER DEFAULT 0,
    last_error TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_connection_provider UNIQUE (connection_id, provider)
);

-- Index for quick lookups
CREATE INDEX idx_webhook_subscriptions_connection ON webhook_subscriptions(connection_id);
CREATE INDEX idx_webhook_subscriptions_status ON webhook_subscriptions(status);
CREATE INDEX idx_webhook_subscriptions_expires ON webhook_subscriptions(expires_at);

-- Comments
COMMENT ON TABLE webhook_subscriptions IS 'Tracks webhook/push notification subscriptions for email providers';
COMMENT ON COLUMN webhook_subscriptions.provider IS 'Email provider: GMAIL or OUTLOOK';
COMMENT ON COLUMN webhook_subscriptions.topic_name IS 'Gmail Pub/Sub topic name';
COMMENT ON COLUMN webhook_subscriptions.history_id IS 'Gmail history ID for incremental sync';
COMMENT ON COLUMN webhook_subscriptions.subscription_id IS 'Microsoft Graph subscription ID';
COMMENT ON COLUMN webhook_subscriptions.client_state IS 'Secret token to validate Outlook notifications';

