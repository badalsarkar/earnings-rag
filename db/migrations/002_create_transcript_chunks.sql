CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS transcript_chunks (
    id              BIGSERIAL       PRIMARY KEY,
    transcript_id   BIGINT          NOT NULL REFERENCES transcripts (id) ON DELETE CASCADE,
    chunk_index     SMALLINT        NOT NULL,
    content         TEXT            NOT NULL,
    embedding       vector(1024),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT now(),
    UNIQUE (transcript_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS transcript_chunks_embedding_idx
    ON transcript_chunks USING hnsw (embedding vector_cosine_ops);
