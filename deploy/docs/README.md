# 📚 Deployment Documentation Index

**Complete guide to deploying and managing the Fan Quoting Application on Google Cloud Platform**

---

## 🎯 Start Here

### New to Deployment?
1. **[Quick Start Guide](QUICK_START.md)** ⭐ - Get up and running in 1 hour
2. **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete step-by-step instructions

### Already Deployed?
- **[Monitoring Guide](../README.md#monitoring)** - Check status and view logs
- **[Database Connection Guide](DATABASE_CONNECTION_GUIDE.md)** - Connect to Cloud SQL locally

---

## 📖 Documentation by Topic

### 🚀 Getting Started
| Document | Description | When to Read |
|----------|-------------|--------------|
| [Quick Start](QUICK_START.md) | Fast deployment checklist (1 hour) | First time deployment |
| [Deployment Guide](DEPLOYMENT_GUIDE.md) | Comprehensive deployment instructions | Need detailed explanations |
| [Configuration Guide](CONFIGURATION_GUIDE.md) | Understanding credentials & secrets | Setting up config.yaml |

### 🔐 Security & Configuration
| Document | Description | When to Read |
|----------|-------------|--------------|
| [API Key Reference](API_KEY_REFERENCE.md) | API key generation and usage | Understanding API authentication |
| [Configuration Guide](CONFIGURATION_GUIDE.md) | Credentials management flow | Configuring dev vs production |
| [GitIgnore Guide](GITIGNORE_GUIDE.md) | Security best practices | Avoiding committed secrets |

### 🗄️ Database Management
| Document | Description | When to Read |
|----------|-------------|--------------|
| [Database Connection Guide](DATABASE_CONNECTION_GUIDE.md) | Connect to Cloud SQL from local machine | Need to query production DB |
| [Deployment Guide - Database Section](DEPLOYMENT_GUIDE.md#step-2-database) | Database initialization | First time setup or reset |

---

## 🔄 Common Workflows

### First Time Deployment
```bash
# 1. Configure passwords
nano deploy/config.yaml

# 2. Follow the quick start
# See: QUICK_START.md
python deploy/scripts/1_setup_gcp.py
python deploy/scripts/2_init_database.py
python deploy/scripts/3_deploy_api.py
python deploy/scripts/4_deploy_ui.py
```
📖 **Read**: [Quick Start Guide](QUICK_START.md)

---

### Updating After Code Changes

**API Changes:**
```bash
python deploy/scripts/3_deploy_api.py
```
📖 **Read**: [Deployment Guide - API Section](DEPLOYMENT_GUIDE.md#step-3-api)

**UI Changes:**
```bash
python deploy/scripts/4_deploy_ui.py  # Shows Streamlit Cloud instructions
```
📖 **Read**: [Deployment Guide - UI Section](DEPLOYMENT_GUIDE.md#step-4-ui)

**Database Schema Changes:**
```bash
python deploy/scripts/2_init_database.py
python deploy/scripts/3_deploy_api.py
```
📖 **Read**: [Deployment Guide - Database Section](DEPLOYMENT_GUIDE.md#step-2-database)

---

### Connecting to Production Database

**Option 1: Direct Connection** (Simple)
```bash
# Get IP address
gcloud sql instances describe fan-quoting-db --format="value(ipAddresses[0].ipAddress)"

# Connect with psql or DB tool
psql -h <IP> -U app_user -d fan_quoting
```

**Option 2: Cloud SQL Proxy** (Recommended)
```bash
# Start proxy
deploy/bin/cloud_sql_proxy.exe --instances=abf-fan-quoting-app:australia-southeast1:fan-quoting-db=tcp:5432

# Connect to localhost:5432
psql -h localhost -U app_user -d fan_quoting
```
📖 **Read**: [Database Connection Guide](DATABASE_CONNECTION_GUIDE.md)

---

### Monitoring & Troubleshooting

**Check Status:**
```bash
python deploy/scripts/5_monitor.py
```

**View Logs:**
```bash
# API logs
gcloud run services logs read quoting-api --project=abf-fan-quoting-app

# Database logs
gcloud sql operations list --instance=fan-quoting-db
```
📖 **Read**: [Deployment Guide - Monitoring Section](DEPLOYMENT_GUIDE.md#monitoring)

---

## 🗂️ Document Descriptions

### Core Guides

#### [Quick Start Guide](QUICK_START.md)
- **Purpose**: Get deployed in under 1 hour
- **Audience**: First-time deployers
- **Contents**: 5-step deployment checklist with minimal explanation
- **Length**: ~230 lines

#### [Deployment Guide](DEPLOYMENT_GUIDE.md)
- **Purpose**: Complete deployment documentation
- **Audience**: Anyone deploying or maintaining the application
- **Contents**: 
  - Prerequisites and setup
  - Step-by-step deployment instructions
  - Architecture overview
  - Troubleshooting
  - Cost management
- **Length**: ~590 lines

#### [Configuration Guide](CONFIGURATION_GUIDE.md)
- **Purpose**: Understand credential and secret management
- **Audience**: Developers configuring local or production environments
- **Contents**:
  - Development vs production credentials
  - API key flow
  - Database credential flow
  - Configuration file explanations
- **Length**: ~580 lines

### Reference Guides

#### [API Key Reference](API_KEY_REFERENCE.md)
- **Purpose**: Quick reference for API key questions
- **Audience**: Anyone confused about API keys
- **Contents**:
  - Where API keys come from
  - Dev vs production API keys
  - Visual diagrams of credential flow
- **Length**: ~410 lines

#### [Database Connection Guide](DATABASE_CONNECTION_GUIDE.md)
- **Purpose**: Connect to Cloud SQL from local machine
- **Audience**: Developers and DBAs
- **Contents**:
  - Direct connection setup
  - Cloud SQL Proxy setup
  - PostgreSQL client configuration
  - Troubleshooting
- **Length**: ~510 lines

#### [GitIgnore Guide](GITIGNORE_GUIDE.md)
- **Purpose**: Security best practices for version control
- **Audience**: All developers
- **Contents**:
  - What files to ignore
  - How to check for exposed secrets
  - Recovery steps if secrets committed
- **Length**: Not yet reviewed

---

## 📁 File Structure

```
deploy/
├── README.md                          # Deployment overview
├── requirements.txt                   # Python dependencies
├── config.yaml                        # Configuration (git-ignored)
├── config.yaml.template              # Template for config
│
├── scripts/                           # Deployment scripts
│   ├── 1_setup_gcp.py                # Initial GCP setup
│   ├── 2_init_database.py            # Database initialization
│   ├── 3_deploy_api.py               # Deploy API to Cloud Run
│   ├── 4_deploy_ui.py                # UI deployment instructions
│   ├── 5_monitor.py                  # Monitoring and logs
│   ├── 6_manage_resources.py         # Start/stop services
│   ├── cleanup.py                    # Delete all resources
│   └── test_deployment.py            # Post-deployment testing
│
├── utils/                             # Helper modules
│   ├── logger.py                     # Colored console output
│   ├── gcp_helper.py                 # GCP API wrapper
│   └── db_helper.py                  # Database operations
│
├── bin/                               # Downloaded executables (git-ignored)
│   └── cloud_sql_proxy.exe           # Cloud SQL Proxy
│
├── docs/                              # Documentation (YOU ARE HERE)
│   ├── README.md                     # This index
│   ├── DEPLOYMENT_GUIDE.md          # Complete deployment guide
│   ├── QUICK_START.md               # Fast deployment checklist
│   ├── CONFIGURATION_GUIDE.md       # Config & secrets
│   ├── API_KEY_REFERENCE.md         # API key workflows
│   ├── DATABASE_CONNECTION_GUIDE.md # DB access
│   ├── GITIGNORE_GUIDE.md           # Security
│   │
│   └── archive/                      # Historical documentation
│       ├── RESTRUCTURE_COMPLETE.md  # Repository restructure notes
│       └── TIMEZONE_DEPLOYMENT.md   # Timezone implementation notes
```

---

## 💡 Tips

### Finding What You Need

**"I need to deploy for the first time"**
→ [Quick Start Guide](QUICK_START.md)

**"I don't understand what an API key is or where it comes from"**
→ [API Key Reference](API_KEY_REFERENCE.md)

**"I need to query the production database"**
→ [Database Connection Guide](DATABASE_CONNECTION_GUIDE.md)

**"I want to understand how credentials work"**
→ [Configuration Guide](CONFIGURATION_GUIDE.md)

**"I need detailed deployment instructions"**
→ [Deployment Guide](DEPLOYMENT_GUIDE.md)

**"I want to make sure I'm not committing secrets"**
→ [GitIgnore Guide](GITIGNORE_GUIDE.md)

---

## 🔗 Related Documentation

- **Project README**: `../README.md` - Deployment overview
- **Workflow Guide**: `../../WORKFLOW_QUICK_REFERENCE.md` - Development workflow
- **Schema Documentation**: `../../../Documentation/quote_data_schema_v3.md`
- **API Documentation**: http://localhost:8080/docs (local) or https://quoting-api-*.run.app/docs (production)

---

## 📝 Documentation Maintenance

**Last Updated**: October 31, 2025  
**Maintained By**: Development Team  

To update this index:
1. Add new documents to the appropriate section
2. Update the file structure diagram
3. Add common workflows if new deployment patterns emerge
4. Keep cross-references accurate

---

**Need Help?**
- Check the [Troubleshooting section](DEPLOYMENT_GUIDE.md#troubleshooting) in the Deployment Guide
- Review the [FAQ section](DEPLOYMENT_GUIDE.md#faq) in the Deployment Guide
- Consult the specific guide for your task above
