-- ============================================================================
-- dashboard :: pre-computed query cache on the shared `workforce` database.
-- Mounted as docker-entrypoint-initdb.d/03_dashboard.sql; idempotent.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS dashboard;

CREATE TABLE IF NOT EXISTS dashboard.cache (
    cache_key   VARCHAR(255) PRIMARY KEY,
    data_json   JSONB NOT NULL,
    row_count   INTEGER,
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON dashboard.cache(expires_at);
