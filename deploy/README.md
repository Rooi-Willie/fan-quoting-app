# 🚀 Deployment Scripts# Deployment Scripts



Automated deployment system for the Fan Quoting Application to Google Cloud Platform.Python-based deployment automation for the Fan Quoting Application.



---## 📁 Files Overview



## 📁 Directory Structure| File | Purpose | When to Run |

|------|---------|-------------|

```| `config.yaml` | Configuration & passwords | Edit before first deployment |

deploy/| `1_setup_gcp.py` | Initial GCP setup | Once (first time) |

├── docs/                       # Documentation| `2_init_database.py` | Create & initialize database | Once (or after cleanup) |

│   ├── DEPLOYMENT_GUIDE.md     # Complete deployment guide (START HERE)| `3_deploy_api.py` | Deploy API to Cloud Run | Every API code change |

│   ├── QUICK_START.md          # Fast deployment checklist| `4_deploy_ui.py` | Instructions for Streamlit deployment | Once + when updating UI |

│   └── GITIGNORE_GUIDE.md      # Security and .gitignore info| `5_monitor.py` | View logs and status | As needed |

│| `6_manage_resources.py` | Start/stop services | Daily/weekly |

├── utils/                      # Helper modules| `cleanup.py` | Delete all resources | Rarely (destructive!) |

│   ├── logger.py               # Colored console output

│   ├── gcp_helper.py           # GCP API wrapper## 🚀 Quick Start

│   └── db_helper.py            # Database operations

│```bash

├── config.yaml                 # Configuration (CHANGE PASSWORDS!)# 1. Install dependencies

├── requirements.txt            # Python dependenciespip install -r requirements.txt

├── Dockerfile.api              # Production Docker image

│# 2. Configure (IMPORTANT!)

├── 1_setup_gcp.py              # Step 1: GCP project setupnano config.yaml  # Change passwords!

├── 2_init_database.py          # Step 2: Database initialization

├── 3_deploy_api.py             # Step 3: Deploy API to Cloud Run# 3. Deploy

├── 4_deploy_ui.py              # Step 4: Deploy UI to Streamlit Cloudpython 1_setup_gcp.py

├── 5_monitor.py                # Monitoring and logspython 2_init_database.py

├── 6_manage_resources.py       # Start/stop/schedule resourcespython 3_deploy_api.py

├── cleanup.py                  # Delete all GCP resourcespython 4_deploy_ui.py  # Follow instructions

└── test_deployment.py          # Post-deployment testing```

```

## 📖 Documentation

---

- **Quick Start**: `../QUICK_START.md` (10-minute overview)

## 🚀 Quick Start- **Full Guide**: `../DEPLOYMENT_GUIDE.md` (comprehensive)



### 1. Install Dependencies## ⚙️ Utilities



```bashThe `utils/` folder contains helper modules:

# Navigate to project root

cd fan-quoting-app- `logger.py` - Beautiful console output

- `gcp_helper.py` - Google Cloud API wrappers

# Install deployment tools- `db_helper.py` - Database operations

pip install -r deploy/requirements.txt

```## 🔐 Security



### 2. Configure Passwords**NEVER commit these files to git:**

- `config.yaml` (contains passwords)

```bash- `cloud_sql_proxy.exe` (binary file)

# Edit config.yaml and change these passwords:- `**/__pycache__/` (Python cache)

notepad deploy\config.yaml

These are automatically excluded by `.gitignore`.

# Change:

# - database.credentials.app_password## 💰 Cost Management

# - database.credentials.root_password

``````bash

# Check current cost estimate

### 3. Run Deployment Scriptspython 6_manage_resources.py --action status



```bash# Stop services (save ~$15/month)

# Step 1: Setup GCP (one-time)python 6_manage_resources.py --action stop

python deploy/1_setup_gcp.py

# Enable auto-shutdown (weekends only)

# Step 2: Initialize database (one-time)python 6_manage_resources.py --action schedule-enable

python deploy/2_init_database.py```



# Step 3: Deploy API## 🆘 Troubleshooting

python deploy/3_deploy_api.py

```bash

# Step 4: Deploy UI (follow instructions)# View logs

python deploy/4_deploy_ui.pypython 5_monitor.py

```

# Test deployment

---python 5_monitor.py  # Choose option 5



## 📚 Documentation# Check configuration

cat config.yaml

- **[DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Complete step-by-step guide```

- **[QUICK_START.md](docs/QUICK_START.md)** - Fast deployment checklist

- **[GITIGNORE_GUIDE.md](docs/GITIGNORE_GUIDE.md)** - Security and git configuration## 🔄 Update Workflow



---```bash

# 1. Make code changes

## 🔒 Security# 2. Test locally with docker-compose

# 3. Commit and push

**CRITICAL:** Never commit `config.yaml` to git!git push origin main



The `.gitignore` file protects:# 4. Deploy API (if API changed)

- `deploy/config.yaml` (passwords)python 3_deploy_api.py

- `ui/.streamlit/secrets.toml` (API key)

# 5. UI auto-deploys on push (Streamlit Cloud)

Verify with:```

```bash

git status --ignored | Select-String "config.yaml"## ❌ Complete Removal

```

```bash

---# Delete EVERYTHING (irreversible!)

python cleanup.py

## 📊 Daily Operations```



### Check Status## 📞 Support

```bash

python deploy/6_manage_resources.py --action statusSee the full deployment guide for detailed troubleshooting and FAQs.

```

### Stop Resources (Save Money)
```bash
python deploy/6_manage_resources.py --action stop
```

### Start Resources
```bash
python deploy/6_manage_resources.py --action start
```

### View Logs
```bash
python deploy/5_monitor.py
```

---

## 💰 Cost Optimization

**Enable Auto-Shutdown:**
```bash
python deploy/6_manage_resources.py --action schedule-enable
```

**Disable Auto-Shutdown:**
```bash
python deploy/6_manage_resources.py --action schedule-disable
```

Default schedule (configurable in `config.yaml`):
- **Shutdown:** 6 PM weekdays
- **Startup:** 8 AM weekdays

---

## 🧪 Testing

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
