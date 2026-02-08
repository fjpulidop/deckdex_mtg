-- DeckDex MTG: sessions table for OAuth (Google refresh tokens keyed by session id)
-- Run with: psql $DATABASE_URL -f migrations/002_sessions_table.sql

CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL UNIQUE,
    google_refresh_token TEXT,
    google_email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'utc'),
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions (session_id);
