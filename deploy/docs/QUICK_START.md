# 🚀 Quick Start Guide - Fan Quoting App Deployment

**Total Time:** ~1 hour  
**Difficulty:** Beginner-friendly  
**Cost:** ~$25/month (first 3 months free with GCP credits)

---

## ⚡ TL;DR - 5 Commands to Deploy

```bash
# 1. Configure passwords
nano deploy/config.yaml  # Change app_password and root_password

# 2. Setup GCP
python deploy/1_setup_gcp.py

# 3. Create database
python deploy/2_init_database.py

# 4. Deploy API
python deploy/3_deploy_api.py

# 5. Deploy UI (follow instructions)
python deploy/4_deploy_ui.py
```

---

## ✅ Pre-Flight Checklist (5 minutes)

```bash
# Install dependencies
cd deploy
pip install -r requirements.txt

# Verify tools
python --version  # Should be 3.11.x
gcloud --version  # Should show Google Cloud SDK

# Update passwords in config.yaml
# CRITICAL: Change these before running anything!
# - database.credentials.app_password
# - database.credentials.root_password
```

---

## 📦 Installation Steps

### Step 1: GCP Setup (20 minutes)

```bash
python deploy/1_setup_gcp.py
```

**You'll be asked to:**
1. Login to Google Cloud (opens browser)
2. Link billing account (get $300 free credits!)
3. Confirm API enablement

**Output:**
```
✓ Project created: abf-fan-quoting-app
✓ APIs enabled
✓ API key generated
```

---

### Step 2: Database (30 minutes)

```bash
python deploy/2_init_database.py
```

**What happens:**
1. Creates Cloud SQL instance (wait 5-10 min)
2. Uploads CSV files
3. Initializes database schema
4. Loads your data

**Output:**
```
✓ Database created
✓ 10 tables loaded
✓ 5,234 rows imported
```

---

### Step 3: API (10 minutes)

```bash
python deploy/3_deploy_api.py
```

**What happens:**
1. Builds Docker container
2. Deploys to Cloud Run
3. Tests endpoints

**Output:**
```
✓ API deployed
✓ URL: https://fan-quoting-api-xyz.run.app
✓ Health check: PASSED
```

---

### Step 4: UI (10 minutes)

```bash
python deploy/4_deploy_ui.py
```

**Follow the interactive guide:**
1. Push code to GitHub
2. Deploy on Streamlit Cloud (manual, 5 minutes)
3. Add secrets (API_BASE_URL, API_KEY)
4. Configure email authentication

**Output:**
```
✓ UI deployed
✓ URL: https://airblowfans-quoting.streamlit.app
✓ Authentication: @airblowfans.co.za only
```

---

## 🎯 First Use

1. Visit your Streamlit app URL
2. Sign in with @airblowfans.co.za email
3. Create a test quote
4. 🎉 Done!

---

## 💰 Save Money

```bash
# Stop services when not in use (saves ~$15/month)
python deploy/6_manage_resources.py --action stop

# Start when needed
python deploy/6_manage_resources.py --action start

# Auto-shutdown schedule (weekends)
python deploy/6_manage_resources.py --action schedule-enable
```

---

## 📊 Monitoring

```bash
# View logs and status
python deploy/5_monitor.py

# Options:
# 1. API logs
# 2. Errors only
# 3. Database operations
# 4. Test endpoints
# 5. Status overview
```

---

## 🔄 Making Updates

```bash
# After changing code:
git add .
git commit -m "Your changes"
git push origin main

# Redeploy API
python deploy/3_deploy_api.py

# UI auto-deploys on git push
```

---

## ❌ Delete Everything

```bash
# If you want to start over or remove the app
python deploy/cleanup.py

# Type 'DELETE' to confirm
```

---

## 🆘 Common Issues

### "API key is missing"
→ Check `.streamlit/secrets.toml` has correct API_KEY

### "Database connection failed"
→ Run: `python deploy/6_manage_resources.py --action status`

### "Deployment failed"
→ Check logs: `python deploy/5_monitor.py`

---

## 📚 Full Documentation

See `DEPLOYMENT_GUIDE.md` for complete details on:
- Architecture
- Security
- Cost optimization
- Troubleshooting
- Advanced configuration

---

## 🎊 That's It!

Your app is now live at:
- **UI**: `https://airblowfans-quoting.streamlit.app`
- **API**: `https://fan-quoting-api-xyz.run.app`

**Monthly Cost**: ~$25 (or ~$10 with auto-shutdown)

**Need help?** Check the full `DEPLOYMENT_GUIDE.md`
