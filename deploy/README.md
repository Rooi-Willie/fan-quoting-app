# 🚀 Deployment Scripts# 🚀 Deployment Scripts# Deployment Scripts



Automated deployment system for the Fan Quoting Application to Google Cloud Platform.



---Automated deployment system for the Fan Quoting Application to Google Cloud Platform.Python-based deployment automation for the Fan Quoting Application.



## 📁 Directory Structure



```---## 📁 Files Overview

deploy/

├── docs/                       # Documentation

│   ├── DEPLOYMENT_GUIDE.md     # Complete deployment guide (START HERE)

│   ├── QUICK_START.md          # Fast deployment checklist## 📁 Directory Structure| File | Purpose | When to Run |

│   └── GITIGNORE_GUIDE.md      # Security and .gitignore info

│|------|---------|-------------|

├── utils/                      # Helper modules

│   ├── logger.py               # Colored console output```| `config.yaml` | Configuration & passwords | Edit before first deployment |

│   ├── gcp_helper.py           # GCP API wrapper

│   └── db_helper.py            # Database operationsdeploy/| `1_setup_gcp.py` | Initial GCP setup | Once (first time) |

│

├── config.yaml                 # Configuration (CHANGE PASSWORDS!)├── docs/                       # Documentation| `2_init_database.py` | Create & initialize database | Once (or after cleanup) |

├── requirements.txt            # Python dependencies

││   ├── DEPLOYMENT_GUIDE.md     # Complete deployment guide (START HERE)| `3_deploy_api.py` | Deploy API to Cloud Run | Every API code change |

├── 1_setup_gcp.py              # Step 1: GCP project setup

├── 2_init_database.py          # Step 2: Database initialization│   ├── QUICK_START.md          # Fast deployment checklist| `4_deploy_ui.py` | Instructions for Streamlit deployment | Once + when updating UI |

├── 3_deploy_api.py             # Step 3: Deploy API to Cloud Run

├── 4_deploy_ui.py              # Step 4: Deploy UI to Streamlit Cloud│   └── GITIGNORE_GUIDE.md      # Security and .gitignore info| `5_monitor.py` | View logs and status | As needed |

├── 5_monitor.py                # Monitoring and logs

├── 6_manage_resources.py       # Start/stop/schedule resources│| `6_manage_resources.py` | Start/stop services | Daily/weekly |

├── cleanup.py                  # Delete all GCP resources

└── test_deployment.py          # Post-deployment testing├── utils/                      # Helper modules| `cleanup.py` | Delete all resources | Rarely (destructive!) |

```

│   ├── logger.py               # Colored console output

**Note:** Cloud Run uses automatic source-based deployment with Google Cloud Buildpacks. No Dockerfile needed!

│   ├── gcp_helper.py           # GCP API wrapper## 🚀 Quick Start

---

│   └── db_helper.py            # Database operations

## 🚀 Quick Start

│```bash

### 1. Install Dependencies

├── config.yaml                 # Configuration (CHANGE PASSWORDS!)# 1. Install dependencies

```bash

# Navigate to project root├── requirements.txt            # Python dependenciespip install -r requirements.txt

cd fan-quoting-app

├── Dockerfile.api              # Production Docker image

# Install deployment tools

pip install -r deploy/requirements.txt│# 2. Configure (IMPORTANT!)

```

├── 1_setup_gcp.py              # Step 1: GCP project setupnano config.yaml  # Change passwords!

### 2. Configure Passwords

├── 2_init_database.py          # Step 2: Database initialization

```bash

# Edit config.yaml and change these passwords:├── 3_deploy_api.py             # Step 3: Deploy API to Cloud Run# 3. Deploy

notepad deploy\config.yaml

├── 4_deploy_ui.py              # Step 4: Deploy UI to Streamlit Cloudpython 1_setup_gcp.py

# Change:

# - database.credentials.app_password├── 5_monitor.py                # Monitoring and logspython 2_init_database.py

# - database.credentials.root_password

```├── 6_manage_resources.py       # Start/stop/schedule resourcespython 3_deploy_api.py



### 3. Run Deployment Scripts├── cleanup.py                  # Delete all GCP resourcespython 4_deploy_ui.py  # Follow instructions



```bash└── test_deployment.py          # Post-deployment testing```

# Step 1: Setup GCP (one-time)

python deploy/1_setup_gcp.py```



# Step 2: Initialize database (one-time)## 📖 Documentation

python deploy/2_init_database.py

---

# Step 3: Deploy API (uses automatic buildpacks)

python deploy/3_deploy_api.py- **Quick Start**: `../QUICK_START.md` (10-minute overview)



# Step 4: Deploy UI (follow instructions)## 🚀 Quick Start- **Full Guide**: `../DEPLOYMENT_GUIDE.md` (comprehensive)

python deploy/4_deploy_ui.py

```



---### 1. Install Dependencies## ⚙️ Utilities



## 📚 Documentation



- **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Complete step-by-step guide```bashThe `utils/` folder contains helper modules:

- **[QUICK_START.md](docs/QUICK_START.md)** - Fast deployment checklist

- **[GITIGNORE_GUIDE.md](docs/GITIGNORE_GUIDE.md)** - Security and git configuration# Navigate to project root



---cd fan-quoting-app- `logger.py` - Beautiful console output



## 🔒 Security- `gcp_helper.py` - Google Cloud API wrappers



**CRITICAL:** Never commit `config.yaml` to git!# Install deployment tools- `db_helper.py` - Database operations



The `.gitignore` file protects:pip install -r deploy/requirements.txt

- `deploy/config.yaml` (passwords)

- `ui/.streamlit/secrets.toml` (API key)```## 🔐 Security



Verify with:

```bash

git status --ignored | Select-String "config.yaml"### 2. Configure Passwords**NEVER commit these files to git:**

```

- `config.yaml` (contains passwords)

---

```bash- `cloud_sql_proxy.exe` (binary file)

## 📊 Daily Operations

# Edit config.yaml and change these passwords:- `**/__pycache__/` (Python cache)

### Check Status

```bashnotepad deploy\config.yaml

python deploy/6_manage_resources.py --action status

```These are automatically excluded by `.gitignore`.



### Stop Resources (Save Money)# Change:

```bash

python deploy/6_manage_resources.py --action stop# - database.credentials.app_password## 💰 Cost Management

```

# - database.credentials.root_password

### Start Resources

```bash``````bash

python deploy/6_manage_resources.py --action start

```# Check current cost estimate



### View Logs### 3. Run Deployment Scriptspython 6_manage_resources.py --action status

```bash

python deploy/5_monitor.py

```

```bash# Stop services (save ~$15/month)

---

# Step 1: Setup GCP (one-time)python 6_manage_resources.py --action stop

## 💰 Cost Optimization

python deploy/1_setup_gcp.py

**Enable Auto-Shutdown:**

```bash# Enable auto-shutdown (weekends only)

python deploy/6_manage_resources.py --action schedule-enable

```# Step 2: Initialize database (one-time)python 6_manage_resources.py --action schedule-enable



**Disable Auto-Shutdown:**python deploy/2_init_database.py```

```bash

python deploy/6_manage_resources.py --action schedule-disable

```

# Step 3: Deploy API## 🆘 Troubleshooting

Default schedule (configurable in `config.yaml`):

- **Shutdown:** 6 PM weekdayspython deploy/3_deploy_api.py

- **Startup:** 8 AM weekdays

```bash

---

# Step 4: Deploy UI (follow instructions)# View logs

## 🧪 Testing

python deploy/4_deploy_ui.pypython 5_monitor.py

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

python deploy/1_setup_gcp.py---```bash

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

python deploy/6_manage_resources.py --action statusSee the full deployment guide for detailed troubleshooting and FAQs.

---

```

## 🔄 Updates & Re-deployment

### Stop Resources (Save Money)

To update the API after code changes:```bash

```bashpython deploy/6_manage_resources.py --action stop

python deploy/3_deploy_api.py```

```

### Start Resources

To update CSV data:```bash

```bashpython deploy/6_manage_resources.py --action start

python deploy/2_init_database.py```

```

### View Logs

The UI auto-deploys when you push to GitHub.```bash

python deploy/5_monitor.py

---```



## 🏗️ How Cloud Run Deployment Works---



Cloud Run uses **automatic source-based deployment**:## 💰 Cost Optimization



1. Script runs `gcloud run deploy --source .`**Enable Auto-Shutdown:**

2. Cloud Run detects it's a Python app (via `requirements.txt`)```bash

3. Google Cloud Buildpacks automatically:python deploy/6_manage_resources.py --action schedule-enable

   - Installs Python 3.11```

   - Installs dependencies from `requirements.txt`

   - Configures uvicorn for FastAPI**Disable Auto-Shutdown:**

   - Optimizes the container for production```bash

4. Deploys to Cloud Runpython deploy/6_manage_resources.py --action schedule-disable

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
python deploy/1_setup_gcp.py
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
python deploy/3_deploy_api.py
```

To update CSV data:
```bash
python deploy/2_init_database.py
```

The UI auto-deploys when you push to GitHub.

---

**Ready to deploy?** Start with [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)! 🚀
