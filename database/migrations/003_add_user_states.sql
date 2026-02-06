-- Migration: Add user_states table for webhook session management
-- Purpose: Store temporary user state (broadcast composition) for created bots using webhooks
-- Date: 2026-02-06

CREATE TABLE IF NOT EXISTS user_states (
    id BIGSERIAL PRIMARY KEY,
    bot_id BIGINT NOT NULL REFERENCES bots(id) ON DELETE CASCADE,
    user_telegram_id BIGINT NOT NULL,
    state_data JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_bot_user_state UNIQUE (bot_id, user_telegram_id)
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_user_states_bot_id ON user_states(bot_id);
CREATE INDEX IF NOT EXISTS idx_user_states_user_telegram_id ON user_states(user_telegram_id);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_user_states_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_user_states_updated_at
    BEFORE UPDATE ON user_states
    FOR EACH ROW
    EXECUTE FUNCTION update_user_states_updated_at();

-- Clean up old states (optional - run periodically)
-- DELETE FROM user_states WHERE updated_at < NOW() - INTERVAL '24 hours';
