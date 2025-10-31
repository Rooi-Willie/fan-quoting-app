# 🚀 Deployment Scripts# 🚀 Deployment Scripts# 🚀 Deployment Scripts# Deployment Scripts



Automated deployment system for the Fan Quoting Application to Google Cloud Platform.



---Automated deployment system for the Fan Quoting Application to Google Cloud Platform.



## 📁 Directory Structure



```---Automated deployment system for the Fan Quoting Application to Google Cloud Platform.Python-based deployment automation for the Fan Quoting Application.

deploy/

├── README.md                          # This file

├── config.yaml                        # Configuration (CHANGE PASSWORDS!)

├── config.yaml.template              # Template for configuration## 📁 Directory Structure

├── requirements.txt                   # Python dependencies

│

├── scripts/                           # Deployment scripts

│   ├── 1_setup_gcp.py                # Step 1: GCP project setup```---## 📁 Files Overview

│   ├── 2_init_database.py            # Step 2: Database initialization

│   ├── 3_deploy_api.py               # Step 3: Deploy API to Cloud Rundeploy/

│   ├── 4_deploy_ui.py                # Step 4: Deploy UI to Streamlit Cloud

│   ├── 5_monitor.py                  # Monitoring and logs├── docs/                       # Documentation

│   ├── 6_manage_resources.py         # Start/stop/schedule resources

│   ├── cleanup.py                    # Delete all GCP resources│   ├── DEPLOYMENT_GUIDE.md     # Complete deployment guide (START HERE)

│   └── test_deployment.py            # Post-deployment testing

││   ├── QUICK_START.md          # Fast deployment checklist## 📁 Directory Structure| File | Purpose | When to Run |

├── utils/                             # Helper modules

│   ├── logger.py                     # Colored console output│   └── GITIGNORE_GUIDE.md      # Security and .gitignore info

│   ├── gcp_helper.py                 # GCP API wrapper

│   └── db_helper.py                  # Database operations│|------|---------|-------------|

│

├── bin/                               # Downloaded executables (git-ignored)├── utils/                      # Helper modules

│   └── cloud_sql_proxy.exe           # Cloud SQL Proxy

││   ├── logger.py               # Colored console output```| `config.yaml` | Configuration & passwords | Edit before first deployment |

└── docs/                              # Documentation

    ├── README.md                     # Documentation index│   ├── gcp_helper.py           # GCP API wrapper

    ├── DEPLOYMENT_GUIDE.md           # Complete deployment guide ⭐ START HERE

    ├── QUICK_START.md                # Fast deployment checklist│   └── db_helper.py            # Database operationsdeploy/| `1_setup_gcp.py` | Initial GCP setup | Once (first time) |

    ├── CONFIGURATION_GUIDE.md        # Config & secrets management

    ├── API_KEY_REFERENCE.md          # API key workflows│

    ├── DATABASE_CONNECTION_GUIDE.md  # Connect to Cloud SQL locally

    ├── GITIGNORE_GUIDE.md            # Security and .gitignore info├── config.yaml                 # Configuration (CHANGE PASSWORDS!)├── docs/                       # Documentation| `2_init_database.py` | Create & initialize database | Once (or after cleanup) |

    │

    └── archive/                       # Historical documentation├── requirements.txt            # Python dependencies

        ├── RESTRUCTURE_COMPLETE.md   # Repository restructure notes

        └── TIMEZONE_DEPLOYMENT.md    # Timezone implementation notes││   ├── DEPLOYMENT_GUIDE.md     # Complete deployment guide (START HERE)| `3_deploy_api.py` | Deploy API to Cloud Run | Every API code change |

```

├── 1_setup_gcp.py              # Step 1: GCP project setup

---

├── 2_init_database.py          # Step 2: Database initialization│   ├── QUICK_START.md          # Fast deployment checklist| `4_deploy_ui.py` | Instructions for Streamlit deployment | Once + when updating UI |

## 🚀 Quick Start

├── 3_deploy_api.py             # Step 3: Deploy API to Cloud Run

### 1. Install Dependencies

├── 4_deploy_ui.py              # Step 4: Deploy UI to Streamlit Cloud│   └── GITIGNORE_GUIDE.md      # Security and .gitignore info| `5_monitor.py` | View logs and status | As needed |

```bash

# Install deployment tools├── 5_monitor.py                # Monitoring and logs

pip install -r deploy/requirements.txt

```├── 6_manage_resources.py       # Start/stop/schedule resources│| `6_manage_resources.py` | Start/stop services | Daily/weekly |



### 2. Configure Passwords├── cleanup.py                  # Delete all GCP resources



```bash└── test_deployment.py          # Post-deployment testing├── utils/                      # Helper modules| `cleanup.py` | Delete all resources | Rarely (destructive!) |

# Edit config.yaml and change these passwords

notepad deploy\config.yaml```



# REQUIRED: Change these two passwords│   ├── logger.py               # Colored console output

# - database.credentials.app_password

# - database.credentials.root_password**Note:** Cloud Run uses automatic source-based deployment with Google Cloud Buildpacks. No Dockerfile needed!

```

│   ├── gcp_helper.py           # GCP API wrapper## 🚀 Quick Start

### 3. Run Deployment Scripts

---

```bash

# Step 1: Setup GCP (one-time)│   └── db_helper.py            # Database operations

python deploy/scripts/1_setup_gcp.py

## 🚀 Quick Start

# Step 2: Initialize database (one-time)

python deploy/scripts/2_init_database.py│```bash



# Step 3: Deploy API### 1. Install Dependencies

python deploy/scripts/3_deploy_api.py

├── config.yaml                 # Configuration (CHANGE PASSWORDS!)# 1. Install dependencies

# Step 4: Deploy UI (follow instructions)

python deploy/scripts/4_deploy_ui.py```bash

```

# Navigate to project root├── requirements.txt            # Python dependenciespip install -r requirements.txt

---

cd fan-quoting-app

## 📖 Documentation

├── Dockerfile.api              # Production Docker image

**New to deployment?**

- 📘 [Quick Start Guide](docs/QUICK_START.md) - Get deployed in 1 hour# Install deployment tools

- 📗 [Complete Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Step-by-step instructions

pip install -r deploy/requirements.txt│# 2. Configure (IMPORTANT!)

**Need help with specific topics?**

- 📚 [Documentation Index](docs/README.md) - Find the right guide for your task```

- 🔐 [Configuration Guide](docs/CONFIGURATION_GUIDE.md) - Understanding credentials

- 🔑 [API Key Reference](docs/API_KEY_REFERENCE.md) - API key questions answered├── 1_setup_gcp.py              # Step 1: GCP project setupnano config.yaml  # Change passwords!

- 🗄️ [Database Connection Guide](docs/DATABASE_CONNECTION_GUIDE.md) - Connect to Cloud SQL

- 🔒 [GitIgnore Guide](docs/GITIGNORE_GUIDE.md) - Security best practices### 2. Configure Passwords



---├── 2_init_database.py          # Step 2: Database initialization



## 🔐 Security```bash



**CRITICAL:** Never commit `config.yaml` to git!# Edit config.yaml and change these passwords:├── 3_deploy_api.py             # Step 3: Deploy API to Cloud Run# 3. Deploy



The `.gitignore` file protects sensitive files:notepad deploy\config.yaml

- `deploy/config.yaml` (database passwords, API keys)

- `deploy/bin/` (binary executables)├── 4_deploy_ui.py              # Step 4: Deploy UI to Streamlit Cloudpython 1_setup_gcp.py

- `ui/.streamlit/secrets.toml` (Streamlit secrets)

# Change:

Verify with:

```bash# - database.credentials.app_password├── 5_monitor.py                # Monitoring and logspython 2_init_database.py

git status --ignored | findstr config.yaml

```# - database.credentials.root_password



See [GitIgnore Guide](docs/GITIGNORE_GUIDE.md) for complete security checklist.```├── 6_manage_resources.py       # Start/stop/schedule resourcespython 3_deploy_api.py



---



## 🛠️ Script Reference### 3. Run Deployment Scripts├── cleanup.py                  # Delete all GCP resourcespython 4_deploy_ui.py  # Follow instructions



| Script | Purpose | When to Run |

|--------|---------|-------------|

| `1_setup_gcp.py` | Initial GCP project setup | Once (first time) |```bash└── test_deployment.py          # Post-deployment testing```

| `2_init_database.py` | Create & initialize database | Once (or after cleanup) |

| `3_deploy_api.py` | Deploy API to Cloud Run | After API code changes |# Step 1: Setup GCP (one-time)

| `4_deploy_ui.py` | Deploy UI to Streamlit Cloud | Once + when updating UI |

| `5_monitor.py` | View logs and status | As needed for monitoring |python deploy/scripts/_setup_gcp.py```

| `6_manage_resources.py` | Start/stop/schedule services | Daily/weekly cost management |

| `cleanup.py` | Delete all GCP resources | Rarely (destructive!) |

| `test_deployment.py` | Test deployed application | After deployment |

# Step 2: Initialize database (one-time)## 📖 Documentation

---

python deploy/scripts/_init_database.py

## 💡 Common Tasks

---

### Update API After Code Changes

```bash# Step 3: Deploy API (uses automatic buildpacks)

python deploy/scripts/3_deploy_api.py

```python deploy/scripts/_deploy_api.py- **Quick Start**: `../QUICK_START.md` (10-minute overview)



### Update Database Schema

```bash

python deploy/scripts/2_init_database.py# Step 4: Deploy UI (follow instructions)## 🚀 Quick Start- **Full Guide**: `../DEPLOYMENT_GUIDE.md` (comprehensive)

python deploy/scripts/3_deploy_api.py  # Restart API to use new schema

```python deploy/scripts/_deploy_ui.py



### Check Deployment Status```

```bash

python deploy/scripts/5_monitor.py

```

---### 1. Install Dependencies## ⚙️ Utilities

### Stop Services to Save Costs

```bash

python deploy/scripts/6_manage_resources.py --action stop

```## 📚 Documentation



### Start Services

```bash

python deploy/scripts/6_manage_resources.py --action start- **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Complete step-by-step guide```bashThe `utils/` folder contains helper modules:

```

- **[QUICK_START.md](docs/QUICK_START.md)** - Fast deployment checklist

---

- **[GITIGNORE_GUIDE.md](docs/GITIGNORE_GUIDE.md)** - Security and git configuration# Navigate to project root

## 🌐 Architecture



```

User Browser---cd fan-quoting-app- `logger.py` - Beautiful console output

    ↓

Cloudflare DNS (quoting.airblowfans.org)

    ↓

Streamlit Cloud (UI)## 🔒 Security- `gcp_helper.py` - Google Cloud API wrappers

    ↓ (API Key Authentication)

Google Cloud Run (API)

    ↓ (Private Connection)

Google Cloud SQL (Database)**CRITICAL:** Never commit `config.yaml` to git!# Install deployment tools- `db_helper.py` - Database operations

```



**Monthly Cost Estimate:** $18-30/month

The `.gitignore` file protects:pip install -r deploy/requirements.txt

---

- `deploy/config.yaml` (passwords)

## 📊 Monitoring

- `ui/.streamlit/secrets.toml` (API key)```## 🔐 Security

### View Logs

```bash

# API logs

python deploy/scripts/5_monitor.pyVerify with:



# Or use gcloud directly```bash

gcloud run services logs read quoting-api --project=abf-fan-quoting-app

```git status --ignored | Select-String "config.yaml"### 2. Configure Passwords**NEVER commit these files to git:**



### Check Status```

```bash

python deploy/scripts/6_manage_resources.py --action status- `config.yaml` (contains passwords)

```

---

### Access URLs

- **API**: https://quoting-api-*.run.app```bash- `cloud_sql_proxy.exe` (binary file)

- **API Docs**: https://quoting-api-*.run.app/docs

- **UI**: https://quoting.airblowfans.org## 📊 Daily Operations

- **GCP Console**: https://console.cloud.google.com

# Edit config.yaml and change these passwords:- `**/__pycache__/` (Python cache)

---

### Check Status

## 🔗 Related Documentation

```bashnotepad deploy\config.yaml

- **Project README**: [../README.md](../README.md) - Project overview

- **Workflow Guide**: [../WORKFLOW_QUICK_REFERENCE.md](../WORKFLOW_QUICK_REFERENCE.md) - Development workflowpython deploy/scripts/_manage_resources.py --action status

- **Schema Documentation**: [../../Documentation/quote_data_schema_v3.md](../../Documentation/quote_data_schema_v3.md)

```These are automatically excluded by `.gitignore`.

---



## 📞 Need Help?

### Stop Resources (Save Money)# Change:

1. Check the [Documentation Index](docs/README.md) for the right guide

2. Read the [Troubleshooting section](docs/DEPLOYMENT_GUIDE.md#troubleshooting) in the Deployment Guide```bash

3. Review the [FAQ section](docs/DEPLOYMENT_GUIDE.md#faq) in the Deployment Guide

python deploy/scripts/_manage_resources.py --action stop# - database.credentials.app_password## 💰 Cost Management

---

```

**Note:** Cloud Run uses automatic source-based deployment with Google Cloud Buildpacks. No Dockerfile needed!

# - database.credentials.root_password

### Start Resources

```bash``````bash

python deploy/scripts/_manage_resources.py --action start

```# Check current cost estimate



### View Logs### 3. Run Deployment Scriptspython 6_manage_resources.py --action status

```bash

python deploy/scripts/_monitor.py

```

```bash# Stop services (save ~$15/month)

---

# Step 1: Setup GCP (one-time)python 6_manage_resources.py --action stop

## 💰 Cost Optimization

python deploy/scripts/_setup_gcp.py

**Enable Auto-Shutdown:**

```bash# Enable auto-shutdown (weekends only)

python deploy/scripts/_manage_resources.py --action schedule-enable

```# Step 2: Initialize database (one-time)python 6_manage_resources.py --action schedule-enable



**Disable Auto-Shutdown:**python deploy/scripts/_init_database.py```

```bash

python deploy/scripts/_manage_resources.py --action schedule-disable

```

# Step 3: Deploy API## 🆘 Troubleshooting

Default schedule (configurable in `config.yaml`):

- **Shutdown:** 6 PM weekdayspython deploy/scripts/_deploy_api.py

- **Startup:** 8 AM weekdays

```bash

---

# Step 4: Deploy UI (follow instructions)# View logs

## 🧪 Testing

python deploy/scripts/_deploy_ui.pypython 5_monitor.py

After deployment, run:

```bash```

python deploy/test_deployment.py

```# Test deployment



Tests:---python 5_monitor.py  # Choose option 5

- ✅ API health check

- ✅ API authentication

- ✅ Database connection

- ✅ UI accessibility## 📚 Documentation# Check configuration



---cat config.yaml



## 🆘 Troubleshooting- **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Complete step-by-step guide```



### Common Issues- **[QUICK_START.md](docs/QUICK_START.md)** - Fast deployment checklist



**1. "config.yaml not found"**- **[GITIGNORE_GUIDE.md](docs/GITIGNORE_GUIDE.md)** - Security and git configuration## 🔄 Update Workflow

```bash

# Make sure you're in the fan-quoting-app directory

cd fan-quoting-app

python deploy/scripts/_setup_gcp.py---```bash

```

# 1. Make code changes

**2. "Please change default passwords"**

```bash## 🔒 Security# 2. Test locally with docker-compose

# Edit config.yaml and change CHANGE_ME_* passwords

notepad deploy\config.yaml# 3. Commit and push

```

**CRITICAL:** Never commit `config.yaml` to git!git push origin main

**3. "gcloud command not found"**

- Install Google Cloud CLI: https://cloud.google.com/sdk/docs/install

- Run: `gcloud init`

The `.gitignore` file protects:# 4. Deploy API (if API changed)

---

- `deploy/config.yaml` (passwords)python 3_deploy_api.py

## 📞 Support

- `ui/.streamlit/secrets.toml` (API key)

For detailed help, see:

- [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)# 5. UI auto-deploys on push (Streamlit Cloud)



---Verify with:```



## ⚙️ System Requirements```bash



- Python 3.11+git status --ignored | Select-String "config.yaml"## ❌ Complete Removal

- Google Cloud CLI (gcloud)

- Git```

- Active GCP billing account

- Active GitHub account```bash



------# Delete EVERYTHING (irreversible!)



## 🎯 Deployment Flowpython cleanup.py



```## 📊 Daily Operations```

1_setup_gcp.py → 2_init_database.py → 3_deploy_api.py → 4_deploy_ui.py

     ↓                 ↓                    ↓                 ↓

 GCP Project      PostgreSQL           Cloud Run        Streamlit Cloud

   Setup           Database          (Buildpacks)            UI### Check Status## 📞 Support

```

```bash

**Estimated Time:** 45-60 minutes (first deployment)

python deploy/scripts/_manage_resources.py --action statusSee the full deployment guide for detailed troubleshooting and FAQs.

---

```

## 🔄 Updates & Re-deployment

### Stop Resources (Save Money)

To update the API after code changes:```bash

```bashpython deploy/scripts/_manage_resources.py --action stop

python deploy/scripts/_deploy_api.py```

```

### Start Resources

To update CSV data:```bash

```bashpython deploy/scripts/_manage_resources.py --action start

python deploy/scripts/_init_database.py```

```

### View Logs

The UI auto-deploys when you push to GitHub.```bash

python deploy/scripts/_monitor.py

---```



## 🏗️ How Cloud Run Deployment Works---



Cloud Run uses **automatic source-based deployment**:## 💰 Cost Optimization



1. Script runs `gcloud run deploy --source .`**Enable Auto-Shutdown:**

2. Cloud Run detects it's a Python app (via `requirements.txt`)```bash

3. Google Cloud Buildpacks automatically:python deploy/scripts/_manage_resources.py --action schedule-enable

   - Installs Python 3.11```

   - Installs dependencies from `requirements.txt`

   - Configures uvicorn for FastAPI**Disable Auto-Shutdown:**

   - Optimizes the container for production```bash

4. Deploys to Cloud Runpython deploy/scripts/_manage_resources.py --action schedule-disable

```

**Benefits:**

- ✅ No Dockerfile maintenanceDefault schedule (configurable in `config.yaml`):

- ✅ Google handles optimizations- **Shutdown:** 6 PM weekdays

- ✅ Automatic security updates- **Startup:** 8 AM weekdays

- ✅ Best practices built-in

---

---

## 🧪 Testing

**Ready to deploy?** Start with [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)! 🚀

After deployment, run:
```bash
python deploy/test_deployment.py
```

Tests:
- ✅ API health check
- ✅ API authentication
- ✅ Database connection
- ✅ UI accessibility

---

## 🆘 Troubleshooting

### Common Issues

**1. "config.yaml not found"**
```bash
# Make sure you're in the fan-quoting-app directory
cd fan-quoting-app
python deploy/scripts/_setup_gcp.py
```

**2. "Please change default passwords"**
```bash
# Edit config.yaml and change CHANGE_ME_* passwords
notepad deploy\config.yaml
```

**3. "gcloud command not found"**
- Install Google Cloud CLI: https://cloud.google.com/sdk/docs/install
- Run: `gcloud init`

---

## 📞 Support

For detailed help, see:
- [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) (if exists)

---

## ⚙️ System Requirements

- Python 3.11+
- Google Cloud CLI (gcloud)
- Git
- Active GCP billing account
- Active GitHub account

---

## 🎯 Deployment Flow

```
1_setup_gcp.py → 2_init_database.py → 3_deploy_api.py → 4_deploy_ui.py
     ↓                 ↓                    ↓                 ↓
 GCP Project      PostgreSQL           Cloud Run        Streamlit Cloud
   Setup           Database               API                 UI
```

**Estimated Time:** 45-60 minutes (first deployment)

---

## 🔄 Updates & Re-deployment

To update the API after code changes:
```bash
python deploy/scripts/_deploy_api.py
```

To update CSV data:
```bash
python deploy/scripts/_init_database.py
```

The UI auto-deploys when you push to GitHub.

---

**Ready to deploy?** Start with [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)! 🚀
