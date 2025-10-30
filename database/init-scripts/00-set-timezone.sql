-- Set PostgreSQL timezone to South Africa (SAST / Africa/Johannesburg)
-- This ensures all timestamps are displayed in South African time
-- File starts with 00- to run before other init scripts

ALTER DATABASE quoting_db SET timezone TO 'Africa/Johannesburg';

-- Confirmation
DO $$
BEGIN
    RAISE NOTICE 'Database timezone set to Africa/Johannesburg (SAST / UTC+2)';
END $$;
