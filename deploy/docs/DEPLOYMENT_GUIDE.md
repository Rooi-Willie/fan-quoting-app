# 🚀 Fan Quoting Application - Complete Deployment Guide

**Version:** 1.0.0  
**Last Updated:** October 2025  
**Deployment Platform:** Google Cloud Platform + Streamlit Cloud

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Initial Setup](#initial-setup)
5. [Deployment Steps](#deployment-steps)
6. [Post-Deployment](#post-deployment)
7. [Daily Operations](#daily-operations)
8. [Cost Management](#cost-management)
9. [Troubleshooting](#troubleshooting)
10. [Security](#security)

---

## Overview

This application consists of three main components:

- **UI (Streamlit)**: User interface hosted on Streamlit Cloud
- **API (FastAPI)**: Backend hosted on Google Cloud Run
- **Database (PostgreSQL)**: Data storage on Google Cloud SQL

**Monthly Cost Estimate:** $18-30/month

---

## Prerequisites

### Required Accounts

- [ ] Google Account (create at: console.cloud.google.com)
- [ ] GitHub Account (your code repository)
- [ ] Cloudflare Account (for domain management)

### Required Software

```bash
# 1. Python 3.11
python --version  # Should show 3.11.x

# 2. Git
git --version

# 3. Google Cloud CLI
gcloud --version

# 4. pip packages for deployment
cd deploy
pip install -r requirements.txt
```

### Installation Links

- **Google Cloud CLI**: https://cloud.google.com/sdk/docs/install
- **Python 3.11**: https://www.python.org/downloads/
- **Git**: https://git-scm.com/downloads

---

## Architecture

```
User Browser
    ↓
Cloudflare DNS (quoting.airblowfans.org)
    ↓
Streamlit Cloud (UI)
    ↓ (API Key Authentication)
Google Cloud Run (API)
    ↓ (Private Connection)
Google Cloud SQL (Database)
```

### Security Layers

1. **User → UI**: Email authentication (@airblowfans.co.za only)
2. **UI → API**: API key in request headers
3. **API → DB**: Private network (no public IP)

---

## Initial Setup

### Step 1: Configure Passwords

```bash
# Edit deploy/config.yaml
# Change these two passwords:
database:
  credentials:
    app_password: "YOUR_SECURE_PASSWORD_HERE"  # Change this!
    root_password: "YOUR_ROOT_PASSWORD_HERE"   # Change this!
```

**⚠️ IMPORTANT**: Use strong passwords (16+ characters, mixed case, numbers, symbols)

### Step 2: Prepare Repository

```bash
# Ensure you're on the main branch
git checkout main
git pull origin main

# Merge your feature branch
git merge feature/sidebar-relocation-quote-data-new-schema

# Verify all files are committed
git status
```

### Step 3: Verify File Structure

```
fan-quoting-app/
├── deploy/                  ← Deployment scripts & documentation
│   ├── docs/                ← All deployment documentation
│   │   ├── DEPLOYMENT_GUIDE.md (this file)
│   │   ├── QUICK_START.md
│   │   └── GITIGNORE_GUIDE.md
│   ├── utils/               ← Helper modules
│   │   ├── logger.py
│   │   ├── gcp_helper.py
│   │   └── db_helper.py
│   ├── config.yaml          ← YOUR PASSWORDS HERE
│   ├── 1_setup_gcp.py
│   ├── 2_init_database.py
│   ├── 3_deploy_api.py
│   ├── 4_deploy_ui.py
│   ├── 5_monitor.py
│   ├── 6_manage_resources.py
│   ├── test_deployment.py
│   └── Dockerfile.api
├── api/                     ← FastAPI backend
├── ui/                      ← Streamlit frontend
├── database/
│   ├── data/                ← CSV files
│   └── init-scripts/        ← SQL initialization
└── .gitignore               ← Security (excludes secrets)
```

---

## Deployment Steps

### Phase 1: Google Cloud Setup (20 minutes)

```bash
# Run the setup script
python deploy/1_setup_gcp.py
```

**What this does:**
1. Login to Google Cloud
2. Create project: `airblowfans-quoting`
3. Enable required APIs (Cloud Run, Cloud SQL, etc.)
4. Generate API key
5. Create service account

**Manual Steps Required:**
- Link billing account (you get $300 free credits!)
- Set up budget alerts ($50/month recommended)

**Expected Output:**
```
✓ Project created
✓ APIs enabled
✓ Service account created
✓ API key generated: abf_xxxxxxxxxxxxx
```

---

### Phase 2: Database Setup (30 minutes)

```bash
# Create and initialize database
python deploy/2_init_database.py
```

**What this does:**
1. Create Cloud SQL instance (5-10 minutes)
2. Create database and user
3. Store credentials in Secret Manager
4. Upload CSV files to Cloud Storage
5. Run SQL initialization scripts
6. Load data from CSV files

**Expected Output:**
```
✓ Cloud SQL instance created
✓ Database initialized
✓ CSV data loaded
✓ 10 tables created with 5,234 total rows
```

---

### Phase 3: API Deployment (15 minutes)

```bash
# Deploy API to Cloud Run
python deploy/3_deploy_api.py
```

**What this does:**
1. Build Docker container
2. Push to Google Container Registry
3. Deploy to Cloud Run
4. Configure environment variables
5. Test endpoints

**Expected Output:**
```
✓ Deployment complete
✓ API URL: https://fan-quoting-api-abc123-uc.a.run.app
✓ Health check: OK
✓ Database connection: OK
```

**Save this API URL** - you'll need it for Streamlit!

---

### Phase 4: UI Deployment (15 minutes)

```bash
# Get instructions for Streamlit Cloud deployment
python deploy/4_deploy_ui.py
```

**Manual Steps (Follow script instructions):**

1. **Push code to GitHub:**
   ```bash
   git add .
   git commit -m "Prepare for deployment"
   git push origin main
   ```

2. **Deploy to Streamlit Cloud:**
   - Go to: https://share.streamlit.io
   - Sign in with GitHub
   - Click "New app"
   - Configure:
     - Repository: `Rooi-Willie/fan-quoting-app`
     - Branch: `main`
     - Main file: `ui/Login_Page.py`
     - App URL: `airblowfans-quoting`
   
3. **Add Secrets (Advanced Settings):**
   ```toml
   API_BASE_URL = "https://fan-quoting-api-abc123-uc.a.run.app"
   API_KEY = "abf_your_generated_key_from_config"
   ```

4. **Configure Authentication:**
   - Settings → Sharing
   - Enable "Require viewers to log in"
   - Allowed domain: `airblowfans.co.za`

5. **Custom Domain (Optional):**
   - Streamlit: Add domain `quoting.airblowfans.org`
   - Copy CNAME target
   - Cloudflare: Add CNAME record
     - Name: `quoting`
     - Target: (from Streamlit)
     - Proxy: DNS only (gray cloud)

---

## Post-Deployment

### Verification Checklist

- [ ] API health check: `https://your-api.run.app/health`
- [ ] API docs accessible: `https://your-api.run.app/docs`
- [ ] UI loads without errors
- [ ] Can log in with @airblowfans.co.za email
- [ ] Can create a test quote
- [ ] Can view saved quotes
- [ ] Database queries work

### Test the Full Flow

1. Visit your Streamlit app
2. Sign in with your work email
3. Create a new quote
4. Add fan configuration
5. Select motor
6. Save quote
7. View in "Existing Quotes"

---

## Daily Operations

### Making Code Changes

```bash
# 1. Make changes in your IDE
# 2. Test locally
docker-compose up

# 3. Commit and deploy
git add .
git commit -m "Your change description"
git push origin main

# 4. Deploy API (if API changed)
python deploy/3_deploy_api.py

# 5. UI auto-deploys on git push (no action needed)
```

### Viewing Logs

```bash
# Interactive monitoring
python deploy/5_monitor.py

# Options:
# 1. View API logs
# 2. View errors only
# 3. View database operations
# 4. Test endpoints
```

### Managing Costs

```bash
# Check status
python deploy/6_manage_resources.py --action status

# Stop services (save ~$15/month)
python deploy/6_manage_resources.py --action stop

# Start services
python deploy/6_manage_resources.py --action start

# Enable auto-shutdown (weekends)
python deploy/6_manage_resources.py --action schedule-enable
```

---

## Cost Management

### Monthly Cost Breakdown

| Service | Configuration | Cost |
|---------|--------------|------|
| Cloud SQL | db-f1-micro | $7-10 |
| Cloud Run | Min 1 instance | $8-15 |
| Storage | 10GB + CSV files | $2 |
| Networking | Low traffic | $1-2 |
| Streamlit | Community (private) | **FREE** |
| **TOTAL** | | **$18-30** |

### Cost Optimization Strategies

1. **Auto-Shutdown Schedule** (saves ~$12/month):
   ```bash
   python deploy/6_manage_resources.py --action schedule-enable
   ```
   - Stops Friday 6PM, starts Monday 7AM
   - Customizable in `deploy/config.yaml`

2. **Manual Shutdown** (weekends/holidays):
   ```bash
   python deploy/6_manage_resources.py --action stop
   ```

3. **Scale to Zero** (when not in use):
   - Edit `deploy/config.yaml`: set `api.min_instances: 0`
   - Redeploy API

4. **Monitor Usage**:
   - Set budget alerts in GCP Console
   - Review costs monthly: https://console.cloud.google.com/billing

---

## Troubleshooting

### API Can't Connect to Database

```bash
# Check database status
gcloud sql instances describe fan-quoting-db

# Test connection
gcloud sql connect fan-quoting-db --user=app_user

# Verify environment variables
gcloud run services describe fan-quoting-api --region=us-central1
```

### Streamlit Shows "Connection Error"

1. Check API URL in Streamlit secrets
2. Test API directly: `curl https://your-api.run.app/health`
3. Verify API key matches in both config.yaml and Streamlit secrets
4. Check CORS settings in API

### Users Can't Access App

1. Verify email authentication in Streamlit settings
2. Check domain spelling: `airblowfans.co.za`
3. Ask user to log out and back in
4. Ensure user's email is Google-linked

### Deployment Fails

```bash
# View build logs
gcloud builds list --limit=5
gcloud builds log BUILD_ID

# Check service account permissions
gcloud projects get-iam-policy airblowfans-quoting
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "API key is missing" | No X-API-Key header | Check secrets.toml |
| "Invalid API key" | Wrong key | Verify key in config.yaml |
| "Database connection failed" | DB stopped or credentials wrong | Check Cloud SQL status |
| "CORS error" | Origin not allowed | Update middleware.py |

---

## Security

### Security Checklist

- [ ] `deploy/config.yaml` is in `.gitignore`
- [ ] `.streamlit/secrets.toml` is in `.gitignore`
- [ ] Passwords are strong (16+ chars)
- [ ] API key is not in code
- [ ] Streamlit authentication enabled
- [ ] Only @airblowfans.co.za emails allowed
- [ ] Database has no public IP
- [ ] HTTPS enabled on all services
- [ ] Budget alerts configured
- [ ] 2FA enabled on Google account (recommended)

### Password Rotation

```bash
# 1. Update password in config.yaml
# 2. Update in Cloud SQL
gcloud sql users set-password app_user \
  --instance=fan-quoting-db \
  --password=NEW_PASSWORD

# 3. Update secret
echo NEW_PASSWORD | gcloud secrets versions add db-password --data-file=-

# 4. Restart API
python deploy/3_deploy_api.py
```

### API Key Rotation

```bash
# 1. Generate new key in config.yaml
# 2. Update secret
gcloud secrets versions add api-key --data-file=- < new_key.txt

# 3. Update Streamlit secrets
# 4. Restart API
```

---

## Quick Reference Commands

```bash
# Deploy API
python deploy/3_deploy_api.py

# View logs
python deploy/5_monitor.py

# Stop services (save money)
python deploy/6_manage_resources.py --action stop

# Start services
python deploy/6_manage_resources.py --action start

# Delete everything
python deploy/cleanup.py

# Connect to database
gcloud sql connect fan-quoting-db --user=app_user

# View costs
gcloud billing accounts list
# Then visit: https://console.cloud.google.com/billing
```

---

## Support & Resources

### Important URLs

- **API Docs**: https://your-api.run.app/docs
- **Streamlit Dashboard**: https://share.streamlit.io/
- **GCP Console**: https://console.cloud.google.com/
- **Cloud SQL**: https://console.cloud.google.com/sql/instances
- **Cloud Run**: https://console.cloud.google.com/run

### Getting Help

1. Check logs: `python deploy/5_monitor.py`
2. Review troubleshooting section above
3. Check GCP status: https://status.cloud.google.com/
4. Check Streamlit status: https://status.streamlit.io/

---

## Appendix

### File Structure Reference

```
deploy/
├── config.yaml              # Main configuration (PASSWORDS HERE)
├── requirements.txt         # Python dependencies
├── 1_setup_gcp.py          # Initial GCP setup
├── 2_init_database.py      # Database initialization
├── 3_deploy_api.py         # API deployment
├── 4_deploy_ui.py          # UI deployment guide
├── 5_monitor.py            # Monitoring tool
├── 6_manage_resources.py   # Resource management
├── cleanup.py              # Delete all resources
└── utils/
    ├── logger.py           # Logging utilities
    ├── gcp_helper.py       # GCP wrapper functions
    └── db_helper.py        # Database utilities
```

### Configuration File Template

See `deploy/config.yaml` - all settings in one place:
- GCP project settings
- Database configuration
- API settings
- Cost optimization schedules
- Monitoring preferences

---

**🎉 Congratulations! Your application is now deployed and running in the cloud!**

For questions or issues, refer to the Troubleshooting section or check the logs.
