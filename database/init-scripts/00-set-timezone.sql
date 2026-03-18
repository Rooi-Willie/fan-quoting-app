-- Set PostgreSQL timezone to South Africa (SAST / Africa/Johannesburg)
-- This ensures all timestamps are displayed in South African time
-- File starts with 00- to run before other init scripts

SET timezone TO 'Africa/Johannesburg';

-- Dynamically alter the current database's default timezone
DO $$
BEGIN
  EXECUTE format('ALTER DATABASE %I SET timezone TO %L', current_database(), 'Africa/Johannesburg');
END
$$;
