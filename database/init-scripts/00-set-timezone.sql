-- Set PostgreSQL timezone to South Africa (SAST / Africa/Johannesburg)
-- This ensures all timestamps are displayed in South African time
-- File starts with 00- to run before other init scripts

SET timezone TO 'Africa/Johannesburg';

-- Persist timezone as the database-level default
ALTER DATABASE fan_quoting SET timezone TO 'Africa/Johannesburg';
