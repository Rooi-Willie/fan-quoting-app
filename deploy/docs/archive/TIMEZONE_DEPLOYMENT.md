# South Africa Timezone - Deployment Updates

## Summary
Updated deployment scripts to automatically configure Cloud SQL instances with South Africa timezone (Africa/Johannesburg / UTC+2).

## Changes Made

### 1. `deploy/utils/gcp_helper.py`
**Added timezone configuration to Cloud SQL instance creation**

- Modified `create_sql_instance()` to include `--database-flags=timezone=Africa/Johannesburg`
- Added new method `set_database_timezone()` to update timezone on existing instances

**What it does:**
- New instances are created with the correct timezone from the start
- Existing instances can be updated to the correct timezone

### 2. `deploy/2_init_database.py`
**Updated database initialization to verify timezone**

- When instance already exists, automatically sets timezone to Africa/Johannesburg
- New instances get timezone configured during creation

**What it does:**
- Ensures timezone is always correct, whether creating new or using existing instance

### 3. `database/init-scripts/00-set-timezone.sql`
**Database-level timezone configuration**

Already created! This script:
- Runs automatically during database initialization (before schema creation)
- Sets `ALTER DATABASE quoting_db SET timezone TO 'Africa/Johannesburg'`
- Ensures all connections use SAST timezone

## Deployment Flow

### For New Deployments:
```bash
python deploy/2_init_database.py
```

**What happens:**
1. Creates Cloud SQL instance with `timezone=Africa/Johannesburg` flag
2. Connects via Cloud SQL Proxy
3. Runs `00-set-timezone.sql` → sets database-level timezone
4. Runs `01-schema.sql` → creates tables with TIMESTAMPTZ columns
5. Loads CSV data

**Result:** Everything configured correctly from the start! ✅

### For Existing Deployments:
```bash
python deploy/2_init_database.py
```

**What happens:**
1. Detects instance already exists
2. Runs `gcp.set_database_timezone()` → updates instance flag
3. Runs `00-set-timezone.sql` → updates database setting
4. Schema already exists (skipped)

**Result:** Timezone updated without data loss! ✅

## Testing After Deployment

### Verify Instance Timezone:
```bash
gcloud sql instances describe <instance-name> --format="value(settings.databaseFlags)"
```
Expected: `timezone=Africa/Johannesburg`

### Verify Database Timezone:
Connect and run:
```sql
SHOW TIMEZONE;
```
Expected: `Africa/Johannesburg`

### Verify Timestamps:
```sql
SELECT id, quote_ref, creation_date FROM quotes ORDER BY id DESC LIMIT 3;
```
Expected: `2025-10-30 16:45:00+02` (with +02 offset)

## Summary

✅ **Instance Level**: `--database-flags=timezone=Africa/Johannesburg`  
✅ **Database Level**: `ALTER DATABASE ... SET timezone TO 'Africa/Johannesburg'`  
✅ **Schema Level**: `TIMESTAMPTZ` columns (already done)  
✅ **Application Level**: Timezone-aware datetime code (already done)

All layers configured correctly! 🇿🇦
