-- Records when a card's price was last looked up, whether or not it changed.
-- NULL means never checked (treated as stale by the price refresh job).
ALTER TABLE cards ADD COLUMN IF NOT EXISTS price_last_checked_at TIMESTAMPTZ;
