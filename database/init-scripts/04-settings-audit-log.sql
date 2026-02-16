-- 04-settings-audit-log.sql
-- Creates the settings audit log table for tracking changes to rates and settings.
-- This script is idempotent (uses IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS settings_audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(100) NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value VARCHAR(255),
    new_value VARCHAR(255),
    changed_by_user_id INTEGER REFERENCES users(id),
    changed_by_username VARCHAR(50),
    changed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Index for efficient querying by table and time
CREATE INDEX IF NOT EXISTS idx_audit_log_table_time
    ON settings_audit_log (table_name, changed_at DESC);
