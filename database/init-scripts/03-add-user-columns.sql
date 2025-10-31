-- Migration: Add user authentication columns to quotes and users tables
-- This adds columns for the dual authentication system
-- Uses simple ALTER TABLE statements (no DO blocks due to script parser)

-- ========== QUOTES TABLE ==========
-- Add created_by_user_name column (will error if exists, which is caught and ignored)
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS created_by_user_name VARCHAR(255);

-- Add created_by_user_id column (will error if exists, which is caught and ignored)
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS created_by_user_id INTEGER;

-- Add last_modified_by_user_name column (will error if exists, which is caught and ignored)
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS last_modified_by_user_name VARCHAR(255);

-- Add last_modified_by_user_id column (will error if exists, which is caught and ignored)
ALTER TABLE quotes ADD COLUMN IF NOT EXISTS last_modified_by_user_id INTEGER;

-- Create indexes (will error if exists, which is caught and ignored)
CREATE INDEX IF NOT EXISTS idx_quotes_created_by_user_name ON quotes(created_by_user_name);
CREATE INDEX IF NOT EXISTS idx_quotes_created_by_user_id ON quotes(created_by_user_id);
CREATE INDEX IF NOT EXISTS idx_quotes_last_modified_by_user_name ON quotes(last_modified_by_user_name);
CREATE INDEX IF NOT EXISTS idx_quotes_last_modified_by_user_id ON quotes(last_modified_by_user_id);

-- ========== USERS TABLE ==========
-- Add all missing columns from authentication system
ALTER TABLE users ADD COLUMN IF NOT EXISTS username VARCHAR(50) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS job_title VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'user';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS external_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_by INTEGER;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

