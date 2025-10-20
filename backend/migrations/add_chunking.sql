-- Add chunking support for RAG
-- Create table for document chunks with embeddings

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding_vector TEXT NOT NULL,  -- JSON serialized vector
    token_count INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_knowledge_chunks_document_id ON knowledge_chunks (document_id);
CREATE INDEX idx_knowledge_chunks_chunk_index ON knowledge_chunks (document_id, chunk_index);

-- Remove embedding_vector from knowledge_documents (now in chunks)
-- Keep content_text for reference but embeddings are in chunks
ALTER TABLE knowledge_documents DROP COLUMN IF EXISTS embedding_vector;
ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS chunk_count INTEGER DEFAULT 0;

