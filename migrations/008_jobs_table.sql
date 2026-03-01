-- DeckDex MTG: persistent jobs table
-- Run with: psql $DATABASE_URL -f migrations/008_jobs_table.sql

CREATE TABLE IF NOT EXISTS jobs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     INTEGER REFERENCES users(id),
    type        VARCHAR(64) NOT NULL,
    status      VARCHAR(32) NOT NULL DEFAULT 'running',
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    completed_at TIMESTAMP WITH TIME ZONE,
    result      JSONB
);

CREATE INDEX IF NOT EXISTS idx_jobs_user_created ON jobs (user_id, created_at DESC);
