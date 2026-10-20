CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    doc_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL, -- speech, screen, pdf, ppt, notes, code
    text TEXT NOT NULL,
    start_s REAL,
    end_s REAL,
    visible_from_s REAL NOT NULL,
    page INT,
    slide INT,
    frame_path TEXT,
    meta JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(384),
    tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', text)) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chunks_tac ON chunks (video_id, visible_from_s);
CREATE INDEX IF NOT EXISTS idx_chunks_tsv ON chunks USING gin (tsv);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);
