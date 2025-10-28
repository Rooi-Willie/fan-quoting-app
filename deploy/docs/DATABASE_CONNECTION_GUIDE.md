# 🔌 Database Connection Guide

**Purpose:** Connect to the Cloud SQL PostgreSQL database from your local development environment  
**Target Audience:** Developers, Database Administrators  
**Last Updated:** October 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Connection Options](#connection-options)
3. [Option 1: Direct Connection](#option-1-direct-connection-simple)
4. [Option 2: Cloud SQL Proxy](#option-2-cloud-sql-proxy-recommended)
5. [Using PostgreSQL Tools](#using-postgresql-tools)
6. [Troubleshooting](#troubleshooting)
7. [Security Best Practices](#security-best-practices)

---

## Overview

There are two ways to connect to your Cloud SQL database from your local machine:

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Direct Connection** | Simple, no extra software | IP can change, less secure | Quick queries, testing |
| **Cloud SQL Proxy** | Secure, IP never changes, encrypted | Requires setup, must run in background | Development, production access |

---

## Connection Options

### Connection Details

First, get your database credentials from `deploy/config.yaml`:

```yaml
database:
  instance_name: fan-quoting-db
  database_name: fan_quoting
  credentials:
    app_user: app_user
    app_password: YOUR_APP_PASSWORD_HERE    # Set your actual password
    root_user: postgres
    root_password: YOUR_ROOT_PASSWORD_HERE   # Set your actual password
```

**⚠️ IMPORTANT:** Never share these passwords or commit them to git!

---

## Option 1: Direct Connection (Simple)

This method connects directly to the Cloud SQL instance's public IP address.

### Step 1: Get the Database IP Address

```bash
# Get the current IP address
gcloud sql instances describe fan-quoting-db \
  --project=abf-fan-quoting-app \
  --format="value(ipAddresses[0].ipAddress)"
```

**Example output:** `XX.XXX.XXX.XX` (your actual IP will be shown)

### Step 2: Connection Parameters

Use these settings in any PostgreSQL client:

- **Host/Server:** (IP address from Step 1, e.g., `34.133.198.8`)
- **Port:** `5432`
- **Database:** `fan_quoting`
- **Username:** `app_user`
- **Password:** (from config.yaml)
- **SSL Mode:** `prefer` or `disable`

### Step 3: Test Connection (Command Line)

```bash
# Using psql (if installed)
psql -h YOUR_IP_ADDRESS -U app_user -d fan_quoting

# Enter password when prompted
```

### Step 4: VS Code PostgreSQL Extension

1. Install the **PostgreSQL** extension (by Chris Kolkman)
2. Click the PostgreSQL icon in the sidebar
3. Click "Add Connection"
4. Fill in the connection form:
   - **Server Name:** (your database IP from Step 1)
   - **Authentication Type:** `Password`
   - **User Name:** `app_user`
   - **Password:** (from config.yaml - YOUR_APP_PASSWORD_HERE)
   - **Database Name:** `fan_quoting`
   - **Connection Name:** `Cloud SQL - Fan Quoting (Direct)`
   - **Server Group:** `Servers`
5. Click "Advanced" if needed:
   - **Port:** `5432`
   - **SSL Mode:** `disable`
6. Click "Save & Connect"

### ⚠️ Limitations

- **IP can change** if the instance is recreated or reconfigured
- **Less secure** - connection is not encrypted by default
- **Requires firewall rules** - currently allows connections from anywhere (`0.0.0.0/0`)

---

## Option 2: Cloud SQL Proxy (Recommended)

The Cloud SQL Proxy creates a secure, encrypted tunnel to your database using your Google Cloud credentials.

### Why Use the Proxy?

✅ **Stable connection** - Always use `localhost`, IP never changes  
✅ **Encrypted** - All traffic is encrypted via Google's infrastructure  
✅ **Secure** - Uses your Google Cloud credentials (IAM)  
✅ **No firewall rules** - Works from anywhere  
✅ **Best practice** - Recommended by Google for production access

### One-Time Setup

#### Step 1: Download Cloud SQL Proxy

**For Windows:**
```bash
# Download the Windows executable
curl -o cloud-sql-proxy.exe https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.2/cloud-sql-proxy.x64.exe

# Move to your project directory
move cloud-sql-proxy.exe "fan-quoting-app\cloud-sql-proxy.exe"
```

**For macOS:**
```bash
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.2/cloud-sql-proxy.darwin.amd64

chmod +x cloud-sql-proxy
mv cloud-sql-proxy fan-quoting-app/
```

**For Linux:**
```bash
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.14.2/cloud-sql-proxy.linux.amd64

chmod +x cloud-sql-proxy
mv cloud-sql-proxy fan-quoting-app/
```

#### Step 2: Authenticate with Google Cloud

```bash
# Set up application default credentials
gcloud auth application-default login

# This will open a browser - sign in with your Google account
# Credentials will be saved for future use
```

**✅ You only need to do this once!** The credentials persist until you revoke them.

### Daily Usage

#### Starting the Proxy

Open a terminal and run:

**Windows (PowerShell):**
```powershell
cd "C:\Users\YourName\...\fan-quoting-app"
.\cloud-sql-proxy.exe --port 5432 abf-fan-quoting-app:us-central1:fan-quoting-db
```

**macOS/Linux:**
```bash
cd /path/to/fan-quoting-app
./cloud-sql-proxy --port 5432 abf-fan-quoting-app:us-central1:fan-quoting-db
```

**Expected output:**
```
2025/10/27 14:30:00 [abf-fan-quoting-app:us-central1:fan-quoting-db] Listening on 127.0.0.1:5432
2025/10/27 14:30:00 The proxy has started successfully and is ready for new connections!
```

**✅ Keep this terminal window open!** The proxy runs in the foreground.

#### Connecting via the Proxy

While the proxy is running, use these connection settings:

- **Host/Server:** `localhost` or `127.0.0.1`
- **Port:** `5432`
- **Database:** `fan_quoting`
- **Username:** `app_user`
- **Password:** (from config.yaml)
- **SSL Mode:** `disable` (not needed since proxy encrypts)

#### Stopping the Proxy

- **Windows:** Press `Ctrl+C` in the terminal
- **macOS/Linux:** Press `Ctrl+C` in the terminal

Or simply close the terminal window.

### Advanced: Running in Background

**Windows (PowerShell):**
```powershell
Start-Process -FilePath ".\cloud-sql-proxy.exe" `
  -ArgumentList "--port 5432 abf-fan-quoting-app:us-central1:fan-quoting-db" `
  -WindowStyle Hidden
```

**macOS/Linux:**
```bash
nohup ./cloud-sql-proxy --port 5432 abf-fan-quoting-app:us-central1:fan-quoting-db &
```

**To stop background process:**
```bash
# Find the process ID
ps aux | grep cloud-sql-proxy

# Kill it
kill <PID>
```

---

## Using PostgreSQL Tools

### VS Code PostgreSQL Extension

**With Proxy Running:**

1. Start the Cloud SQL Proxy (see above)
2. In VS Code, install **PostgreSQL** extension
3. Add new connection:
   - **Server Name:** `localhost`
   - **Authentication Type:** `Password`
   - **User Name:** `app_user`
   - **Password:** (from config.yaml)
   - **Database Name:** `fan_quoting`
   - **Connection Name:** `Cloud SQL - Fan Quoting (Proxy)`
   - **Port:** `5432`
   - **SSL Mode:** `disable`
4. Save & Connect

### DBeaver

1. Download from: https://dbeaver.io/download/
2. Create New Connection → PostgreSQL
3. Connection Settings:
   - **Host:** `localhost` (if using proxy) or `YOUR_DB_IP` (direct)
   - **Port:** `5432`
   - **Database:** `fan_quoting`
   - **Username:** `app_user`
   - **Password:** (from config.yaml)
4. Test Connection → Finish

### pgAdmin

1. Download from: https://www.pgadmin.org/download/
2. Right-click "Servers" → Create → Server
3. General tab:
   - **Name:** `Cloud SQL - Fan Quoting`
4. Connection tab:
   - **Host:** `localhost` or `YOUR_DB_IP`
   - **Port:** `5432`
   - **Maintenance database:** `fan_quoting`
   - **Username:** `app_user`
   - **Password:** (from config.yaml)
   - **Save password:** ✓
5. Save

### Command Line (psql)

```bash
# With proxy running
psql -h localhost -U app_user -d fan_quoting

# Direct connection (use your actual database IP)
psql -h YOUR_DB_IP -U app_user -d fan_quoting

# Run a single query
psql -h localhost -U app_user -d fan_quoting -c "SELECT COUNT(*) FROM fan_configurations;"

# Execute a SQL file
psql -h localhost -U app_user -d fan_quoting -f script.sql
```

---

## Troubleshooting

### Proxy Won't Start

**Error: "could not find default credentials"**

```bash
# Solution: Authenticate with Google Cloud
gcloud auth application-default login
```

**Error: "failed to dial: compute: Received 403"**

```bash
# Solution: Ensure your account has permission
gcloud projects add-iam-policy-binding abf-fan-quoting-app \
  --member="user:your-email@airblowfans.co.za" \
  --role="roles/cloudsql.client"
```

**Error: "port 5432 is already in use"**

```bash
# Solution: Use a different port
.\cloud-sql-proxy.exe --port 5433 abf-fan-quoting-app:us-central1:fan-quoting-db

# Then connect using port 5433 instead of 5432
```

### Connection Refused

**Check database status:**
```bash
gcloud sql instances describe fan-quoting-db --project=abf-fan-quoting-app
```

Look for `state: RUNNABLE` in the output.

**If stopped, start it:**
```bash
gcloud sql instances patch fan-quoting-db --activation-policy=ALWAYS
```

### Can't Connect - Direct Connection

**Verify IP address:**
```bash
gcloud sql instances describe fan-quoting-db \
  --project=abf-fan-quoting-app \
  --format="value(ipAddresses[0].ipAddress)"
```

**Check your IP is allowed:**
```bash
gcloud sql instances describe fan-quoting-db --format="value(settings.ipConfiguration.authorizedNetworks)"
```

Should show `0.0.0.0/0` (allows all IPs).

### Authentication Failed

1. **Verify password:**
   - Check `deploy/config.yaml` for correct password
   - Passwords are case-sensitive

2. **Reset password if needed:**
   ```bash
   gcloud sql users set-password app_user \
     --instance=fan-quoting-db \
     --password=NEW_PASSWORD_HERE
   
   # Update config.yaml with new password
   ```

### Proxy Connection Hangs

1. **Check proxy is running:**
   - Look for "ready for new connections" message
   - Proxy terminal should be open

2. **Verify connection name:**
   ```bash
   # Should be: abf-fan-quoting-app:us-central1:fan-quoting-db
   gcloud sql instances describe fan-quoting-db --format="value(connectionName)"
   ```

3. **Try restarting proxy:**
   - Stop: `Ctrl+C`
   - Start again

---

## Security Best Practices

### ✅ DO

- **Use Cloud SQL Proxy** for regular development work
- **Keep credentials in config.yaml** (already in .gitignore)
- **Use strong passwords** (16+ characters, mixed case, numbers, symbols)
- **Enable 2FA** on your Google account
- **Rotate passwords** every 90 days
- **Use read-only user** for querying (create if needed)
- **Limit connection time** - disconnect when done

### ❌ DON'T

- **Don't commit passwords** to git
- **Don't share database credentials** via email/Slack
- **Don't use weak passwords** like `password123`
- **Don't leave proxy running** when not in use
- **Don't use root user** for daily work
- **Don't modify production data** without backup

### Creating a Read-Only User

For safe querying without risk of accidental modifications:

```sql
-- Connect as postgres user first
CREATE USER readonly_user WITH PASSWORD 'your_secure_password';
GRANT CONNECT ON DATABASE fan_quoting TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;
```

Then use `readonly_user` for queries instead of `app_user`.

---

## Quick Reference

### Common Connection Strings

**Python (SQLAlchemy) - with Proxy:**
```python
DATABASE_URL = "postgresql://app_user:password@localhost:5432/fan_quoting"
```

**Python (psycopg2) - with Proxy:**
```python
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="fan_quoting",
    user="app_user",
    password="your_password"
)
```

**Node.js (pg) - with Proxy:**
```javascript
const client = new Client({
  host: 'localhost',
  port: 5432,
  database: 'fan_quoting',
  user: 'app_user',
  password: 'your_password'
});
```

### Useful SQL Queries

```sql
-- List all tables
\dt

-- Count rows in each table
SELECT 
    schemaname,
    tablename,
    n_tup_ins AS "Total Rows"
FROM pg_stat_user_tables
ORDER BY n_tup_ins DESC;

-- Check database size
SELECT pg_size_pretty(pg_database_size('fan_quoting'));

-- List recent queries
SELECT pid, usename, query, state
FROM pg_stat_activity
WHERE datname = 'fan_quoting';

-- View fan configurations
SELECT uid, fan_size_mm, hub_size_mm 
FROM fan_configurations 
ORDER BY fan_size_mm;
```

---

## Additional Resources

- **Cloud SQL Proxy Documentation:** https://cloud.google.com/sql/docs/postgres/sql-proxy
- **PostgreSQL Client Tools:** https://www.postgresql.org/download/
- **VS Code PostgreSQL Extension:** https://marketplace.visualstudio.com/items?itemName=ckolkman.vscode-postgres
- **DBeaver:** https://dbeaver.io/
- **pgAdmin:** https://www.pgadmin.org/

---

**📝 Summary:**

- **Quick & Simple:** Use direct connection with database IP (get from `gcloud`)
- **Secure & Recommended:** Use Cloud SQL Proxy with `localhost`
- **Both methods** use the same credentials from `config.yaml`
- **Proxy advantage:** Encrypted, stable, works from anywhere
- **Keep proxy running** in a terminal while connected

**Need help?** Check the [Deployment Guide](DEPLOYMENT_GUIDE.md) troubleshooting section.
