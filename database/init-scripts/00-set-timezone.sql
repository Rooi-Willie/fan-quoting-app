-- Set PostgreSQL timezone to South Africa (SAST / Africa/Johannesburg)
-- This ensures all timestamps are displayed in South African time
-- File starts with 00- to run before other init scripts

ALTER DATABASE fan_quoting SET timezone TO 'Africa/Johannesburg';
