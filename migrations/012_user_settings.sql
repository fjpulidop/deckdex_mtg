-- Migration 012: Per-user settings table (JSONB)
-- Stores user preferences like external API toggles.

CREATE TABLE IF NOT EXISTS user_settings (
    user_id   INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    settings  JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);
