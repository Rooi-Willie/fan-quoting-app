# 🔐 Configuration & Secrets Management Guide

**Complete guide to understanding credentials, API keys, and configuration flow**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Development vs Production](#development-vs-production)
3. [API Key Flow](#api-key-flow)
4. [Database Credentials Flow](#database-credentials-flow)
5. [Configuration Files Explained](#configuration-files-explained)
6. [Troubleshooting](#troubleshooting)

---

## Overview

Your application uses **different credentials** for development and production:

- **Development (Local Docker)**: Simple credentials stored in `.env` and `secrets.toml`
- **Production (GCP)**: Secure credentials stored in GCP Secret Manager

### Key Principle

> **Credentials flow in ONE DIRECTION**: From configuration → Environment → Application
> 
> Never hardcode credentials in application code!

---

## Development vs Production

### 🏠 Local Development Environment

**What you're running:**
```
Docker Compose
├── PostgreSQL Database (localhost:5433)
├── FastAPI Backend (localhost:8080)
└── Streamlit UI (localhost:8501)
```

**Credential Storage:**
- `.env` file (in `fan-quoting-app/` directory)
- `secrets.toml` file (in `ui/.streamlit/` directory)

**Why two files?**
- `.env` → Used by Docker Compose (API and Database containers)
- `secrets.toml` → Used by Streamlit UI (not containerized in dev)

---

### ☁️ Production Environment (GCP)

**What will be deployed:**
```
Google Cloud Platform
├── Cloud SQL (PostgreSQL) - Private network
├── Cloud Run (FastAPI API) - Public with API key
└── Streamlit Cloud (UI) - Public with email auth
```

**Credential Storage:**
- GCP Secret Manager (database passwords, API key)
- Streamlit Cloud Secrets Dashboard (API key, API URL)
- Cloud Run Environment Variables (references to secrets)

---

## API Key Flow

### Question 1: "Does 1_setup_gcp.py create an API key I need to copy?"

**YES! Here's the complete flow:**

### Development API Key (What you have now)

```
.env file:
API_KEY=dev-local-key-12345

secrets.toml file:
API_KEY = "dev-local-key-12345"
```

**This is a simple placeholder for local testing.**

---

### Production API Key (What happens during deployment)

#### Step 1: Generate Secure Key

When you run `python deploy/scripts/_setup_gcp.py`, it:

```python
# Generates a secure 48-character random key
api_key = "abf_" + random_48_chars()
# Example: "abf_xK9mP2wQ7nF4jL8sY3vR5tU1oI6eA2dH4gJ9mN7pQ3sW"
```

This key is saved to `deploy/config.yaml`:

```yaml
api:
  api_key: "abf_xK9mP2wQ7nF4jL8sY3vR5tU1oI6eA2dH4gJ9mN7pQ3sW"
```

#### Step 2: Store in GCP Secret Manager

When you run `python deploy/scripts/_deploy_api.py`, it:

1. Reads the API key from `config.yaml`
2. Stores it in GCP Secret Manager as `API_KEY`
3. Configures Cloud Run to load it as environment variable

#### Step 3: Configure Streamlit Cloud

When you run `python deploy/scripts/_deploy_ui.py`, it **displays instructions**:

```bash
===========================================
MANUAL STEP: Configure Streamlit Secrets
===========================================

Go to your Streamlit Cloud dashboard:
https://share.streamlit.io → Your App → Settings → Secrets

Add these secrets:

API_BASE_URL = "https://fan-quoting-api-abc123-uc.a.run.app"
API_KEY = "abf_xK9mP2wQ7nF4jL8sY3vR5tU1oI6eA2dH4gJ9mN7pQ3sW"
```

**You manually copy the API key** from the script output and paste it into Streamlit Cloud's secrets dashboard.

---

### Why Manual Copy for Streamlit?

**Security reasons:**

1. **Separation of Concerns**: GCP and Streamlit Cloud are separate platforms
2. **No API Access**: Streamlit Cloud doesn't provide an API to programmatically set secrets
3. **User Control**: You explicitly see and approve what credentials are being used

**The flow:**

```
1_setup_gcp.py (generates key)
     ↓
config.yaml (stores key)
     ↓
3_deploy_api.py (uploads to GCP Secret Manager)
     ↓
4_deploy_ui.py (shows you the key to copy)
     ↓
You manually paste into Streamlit Cloud dashboard
```

---

## Database Credentials Flow

### Development Database

**Your current `.env` file:**

```bash
# Database container credentials
POSTGRES_DB=quoting_db
POSTGRES_USER=devuser
POSTGRES_PASSWORD=devpassword

# Connection string for API (Docker internal networking)
DATABASE_URL=postgresql://devuser:devpassword@db:5432/quoting_db
```

**How it works:**

1. Docker Compose reads `.env`
2. Creates PostgreSQL container with these credentials
3. API container reads same `.env` file
4. API connects to database using `@db:5432` (Docker service name)

---

### Production Database

**Your `deploy/config.yaml` file:**

```yaml
database:
  credentials:
    app_user: "app_user"
    app_password: "CHANGE_ME_AppPassword_123!SecureRandom"  # ← You change this
    root_user: "postgres"
    root_password: "CHANGE_ME_RootPassword_456!SecureRandom"  # ← You change this
```

**What happens during deployment:**

#### Step 1: You Set Passwords (Before deployment)

Edit `config.yaml` with strong passwords:

```yaml
database:
  credentials:
    app_user: "app_user"
    app_password: "Xm9$kP2#wQ7nF4@jL8sY3vR"  # ← Your strong password
    root_password: "Zn8!pR5%tU1oI6$eA2dH4gJ"  # ← Your strong password
```

#### Step 2: Create Cloud SQL Instance

When you run `python deploy/scripts/_init_database.py`:

1. Creates Cloud SQL instance with `root_password`
2. Creates application database user with `app_password`
3. Stores both passwords in **GCP Secret Manager**:
   - Secret name: `DB_PASSWORD` → Value: `Xm9$kP2#wQ7nF4@jL8sY3vR`
   - Secret name: `DB_ROOT_PASSWORD` → Value: `Zn8!pR5%tU1oI6$eA2dH4gJ`

#### Step 3: Configure Cloud Run

When you run `python deploy/scripts/_deploy_api.py`:

Cloud Run environment variables are set:

```bash
DB_USER=app_user
DB_NAME=fan_quoting
DB_HOST=  # Not used (Cloud SQL uses Unix socket)
CLOUD_SQL_CONNECTION_NAME=abf-fan-quoting-app:us-central1:fan-quoting-db

# This references the secret:
DB_PASSWORD → points to → Secret Manager: DB_PASSWORD
```

#### Step 4: API Connects to Database

The API's `config.py` detects production mode and uses:

```python
if self.cloud_sql_connection_name:
    # Production: Unix socket connection
    url = f"postgresql+psycopg2://{app_user}:{app_password}@/{db_name}?host=/cloudsql/{connection_name}"
else:
    # Development: TCP connection
    url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
```

---

## Configuration Files Explained

### Local Development Files

#### `.env` (Root Directory)

**Purpose:** Docker Compose configuration

```bash
# Database credentials (used by db container and api container)
POSTGRES_DB=quoting_db
POSTGRES_USER=devuser
POSTGRES_PASSWORD=devpassword

# API configuration (used by api container)
API_KEY=dev-local-key-12345

# Connection strings (convenience, not always used)
DATABASE_URL=postgresql://devuser:devpassword@db:5432/quoting_db
```

**Who uses it:**
- Docker Compose (reads and passes to containers)
- API container (FastAPI backend)
- Database container (PostgreSQL)

**Security:** ✅ In `.gitignore` (never committed)

---

#### `ui/.streamlit/secrets.toml`

**Purpose:** Streamlit UI local development

```toml
# API connection for local development
API_BASE_URL = "http://api:8080"
API_KEY = "dev-local-key-12345"
```

**Who uses it:**
- Streamlit UI (when running locally)

**Security:** ✅ In `.gitignore` (never committed)

---

### Production Configuration Files

#### `deploy/config.yaml`

**Purpose:** Deployment configuration and generated secrets storage

```yaml
# These you set before deployment:
database:
  credentials:
    app_password: "YOUR_STRONG_PASSWORD_HERE"
    root_password: "YOUR_STRONG_ROOT_PASSWORD_HERE"

# This gets generated during deployment:
api:
  api_key: "abf_generated_during_1_setup_gcp"
```

**Who uses it:**
- Deployment scripts (1_setup_gcp.py, 2_init_database.py, etc.)
- You (to copy API key to Streamlit Cloud)

**Security:** ⚠️ **In `.gitignore`** but you should also:
- Never commit this file
- Use different passwords than development
- Rotate passwords periodically

---

#### GCP Secret Manager (Production)

**Purpose:** Secure credential storage in Google Cloud

**Secrets stored:**

| Secret Name | Value Source | Used By |
|------------|--------------|---------|
| `API_KEY` | Generated by `1_setup_gcp.py` | Cloud Run (API) |
| `DB_PASSWORD` | Your `config.yaml` | Cloud Run (API) |
| `DB_ROOT_PASSWORD` | Your `config.yaml` | Database admin tasks |

**Security:** ✅✅✅ Highest security
- Encrypted at rest
- Automatic key rotation available
- Access logged and audited
- Fine-grained IAM permissions

---

#### Streamlit Cloud Secrets Dashboard (Production)

**Purpose:** Secrets for Streamlit UI in production

**Location:** https://share.streamlit.io → Your App → Settings → Secrets

**Secrets you manually add:**

```toml
API_BASE_URL = "https://fan-quoting-api-abc123-uc.a.run.app"
API_KEY = "abf_copied_from_config_yaml_after_setup"
```

**Security:** ✅ Secure
- Encrypted storage
- Not visible in app code
- Not committed to git

---

## Summary: Complete Credential Flow

### Development (Current)

```
You create:
├── .env (API_KEY=dev-local-key-12345, POSTGRES_USER=devuser, etc.)
└── ui/.streamlit/secrets.toml (API_KEY=dev-local-key-12345)

Docker reads:
├── .env → Creates database with devuser:devpassword
├── .env → API container gets API_KEY=dev-local-key-12345
└── secrets.toml → Streamlit UI gets API_KEY=dev-local-key-12345

Result:
✅ UI sends requests with X-API-Key: dev-local-key-12345
✅ API validates and accepts request
✅ API connects to database with devuser:devpassword
```

---

### Production (After Deployment)

```
Step 1: You prepare
├── Edit deploy/config.yaml (set database passwords)
└── Run 1_setup_gcp.py (generates API key → saves to config.yaml)

Step 2: Deployment scripts run
├── 2_init_database.py → Stores DB passwords in GCP Secret Manager
├── 3_deploy_api.py → Stores API_KEY in GCP Secret Manager
└── 4_deploy_ui.py → Shows you the API_KEY to copy

Step 3: You manually configure Streamlit
└── Paste API_KEY into Streamlit Cloud dashboard

Result:
✅ UI sends requests with X-API-Key: abf_secure_production_key
✅ API validates against GCP Secret Manager
✅ API connects to Cloud SQL via Unix socket with password from Secret Manager
```

---

## Key Differences Table

| Aspect | Development | Production |
|--------|-------------|------------|
| **API Key** | `dev-local-key-12345` (simple) | `abf_xK9m...` (48 chars, secure) |
| **API Key Storage** | `.env` + `secrets.toml` (files) | GCP Secret Manager + Streamlit Secrets |
| **DB Password** | `devpassword` (simple) | `Xm9$kP2#wQ7n...` (complex) |
| **DB Password Storage** | `.env` file | GCP Secret Manager |
| **DB Connection** | TCP `@db:5432` | Unix socket `@/cloudsql/...` |
| **API URL** | `http://api:8080` (local) | `https://...run.app` (public) |
| **Security** | Basic (file-based) | Advanced (Secret Manager, IAM) |

---

## Troubleshooting

### Issue: "401 Unauthorized" in Local Development

**Cause:** API_KEY mismatch between `.env` and `secrets.toml`

**Fix:**

1. Check `.env`:
   ```bash
   API_KEY=dev-local-key-12345
   ```

2. Check `ui/.streamlit/secrets.toml`:
   ```toml
   API_KEY = "dev-local-key-12345"
   ```

3. Restart Docker:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

### Issue: "Database connection failed" in Local Development

**Cause:** Database credentials mismatch

**Fix:**

1. Check `.env` has:
   ```bash
   POSTGRES_DB=quoting_db
   POSTGRES_USER=devuser
   POSTGRES_PASSWORD=devpassword
   ```

2. Restart database:
   ```bash
   docker-compose down
   docker-compose up -d db
   docker-compose up -d api
   ```

3. Check API logs:
   ```bash
   docker logs quoting_api_dev
   ```

---

### Issue: "Cannot find API_KEY in config.yaml"

**Cause:** Haven't run `1_setup_gcp.py` yet

**Expected:** This is normal for development! The production API key is only generated when you start deployment.

**For local dev:** Just use `dev-local-key-12345` as shown above.

---

## Best Practices

### ✅ DO

- Use simple credentials for local development (`dev-local-key-12345`)
- Use strong, unique credentials for production
- Keep `.env` and `secrets.toml` in `.gitignore`
- Rotate production passwords every 90 days
- Copy API key from `config.yaml` to Streamlit (don't type it)

### ❌ DON'T

- Commit `.env` or `secrets.toml` to git
- Use production credentials in development
- Use development credentials in production
- Share your `config.yaml` file
- Hardcode any credentials in source code

---

## Quick Reference

### Development Setup (First Time)

```bash
# 1. Create .env file
cd fan-quoting-app
cat > .env << EOF
POSTGRES_DB=quoting_db
POSTGRES_USER=devuser
POSTGRES_PASSWORD=devpassword
API_KEY=dev-local-key-12345
DATABASE_URL=postgresql://devuser:devpassword@db:5432/quoting_db
EOF

# 2. Create secrets.toml
cat > ui/.streamlit/secrets.toml << EOF
API_BASE_URL = "http://api:8080"
API_KEY = "dev-local-key-12345"
EOF

# 3. Start Docker
docker-compose up -d

# 4. Test
curl http://localhost:8080/health
curl -H "X-API-Key: dev-local-key-12345" http://localhost:8080/fans
```

---

### Production Deployment Checklist

- [ ] Edit `deploy/config.yaml` (set strong passwords)
- [ ] Run `python deploy/scripts/_setup_gcp.py` (generates API key)
- [ ] Note the generated API key from output or `config.yaml`
- [ ] Run `python deploy/scripts/_init_database.py` (stores DB passwords in Secret Manager)
- [ ] Run `python deploy/scripts/_deploy_api.py` (stores API key in Secret Manager)
- [ ] Note the API URL from output
- [ ] Run `python deploy/scripts/_deploy_ui.py` (shows Streamlit setup instructions)
- [ ] Copy API key from output to Streamlit Cloud dashboard
- [ ] Copy API URL to Streamlit Cloud dashboard

---

## Support

If you're still having issues:

1. Check Docker logs:
   ```bash
   docker logs quoting_api_dev
   docker logs quoting_db_dev
   docker logs quoting_ui_dev
   ```

2. Verify environment variables:
   ```bash
   docker exec quoting_api_dev env | grep -E "API_KEY|POSTGRES"
   ```

3. Test database connection:
   ```bash
   docker exec quoting_db_dev psql -U devuser -d quoting_db -c "SELECT version();"
   ```

4. Test API authentication:
   ```bash
   curl -H "X-API-Key: dev-local-key-12345" http://localhost:8080/health
   ```
