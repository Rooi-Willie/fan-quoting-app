-- Migration: Add settings_audit_log table
-- Run this against an existing database that was set up before this feature.
-- Safe to run multiple times (idempotent).
--
-- Usage:
--   Local:    psql -h localhost -p 5433 -U postgres -d quoting_db -f add_settings_audit_log.sql
--   CloudSQL: psql -h <CLOUD_SQL_IP> -U postgres -d quoting_db -f add_settings_audit_log.sql

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

CREATE INDEX IF NOT EXISTS idx_audit_log_table_time
    ON settings_audit_log (table_name, changed_at DESC);

-- Verify
DO $$
BEGIN
    RAISE NOTICE 'settings_audit_log table is ready. Row count: %',
        (SELECT COUNT(*) FROM settings_audit_log);
END $$;
