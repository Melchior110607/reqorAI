-- Add AI Agent fields to requests table
ALTER TABLE requests ADD COLUMN IF NOT EXISTS email_connection_id INTEGER REFERENCES email_connections(id);
ALTER TABLE requests ADD COLUMN IF NOT EXISTS draft_response TEXT;
ALTER TABLE requests ADD COLUMN IF NOT EXISTS draft_generated_at TIMESTAMP WITH TIME ZONE;

-- Add agent tracking to intercepted_emails table
ALTER TABLE intercepted_emails ADD COLUMN IF NOT EXISTS agent_processed BOOLEAN DEFAULT FALSE;
ALTER TABLE intercepted_emails ADD COLUMN IF NOT EXISTS agent_action_taken TEXT;

-- Create knowledge_documents table for RAG
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    content_text TEXT,
    embedding_vector TEXT,
    file_type VARCHAR(50),
    file_size INTEGER,
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster user queries
CREATE INDEX IF NOT EXISTS idx_knowledge_documents_user_id ON knowledge_documents(user_id);

