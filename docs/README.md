# 📚 Fan Quoting Application Documentation

Complete documentation for the Fan Quoting Application project.

---

## 🎯 Quick Navigation

### 👤 I want to...

**...understand the project**
→ [Main README](../README.md)

**...start developing**
→ [Workflow Quick Reference](../WORKFLOW_QUICK_REFERENCE.md)

**...deploy to production**
→ [Deployment Guide](../deploy/docs/DEPLOYMENT_GUIDE.md)

**...understand quote data structure**
→ [Quote Data Schema](../../Documentation/quote_data_schema_v3.md)

---

## 📖 Documentation by Category

### 🚀 Getting Started
- [Main README](../README.md) - Project overview and quick start
- [Workflow Quick Reference](../WORKFLOW_QUICK_REFERENCE.md) - Development workflow commands

### 💻 Development
- [API Documentation](http://localhost:8080/docs) - FastAPI interactive docs (when running locally)
- [Quote Data Schema](../../Documentation/quote_data_schema_v3.md) - Complete quote data structure

### 🚢 Deployment
- [Deployment Documentation Index](../deploy/docs/README.md) - All deployment guides
- [Quick Start](../deploy/docs/QUICK_START.md) - Deploy in 1 hour
- [Complete Deployment Guide](../deploy/docs/DEPLOYMENT_GUIDE.md) - Step-by-step instructions

### 🔧 Features & Implementation

#### Implemented Features
- [Dual Authentication](features/dual-authentication.md) - Email + API key authentication
- [Export Functionality](features/export-functionality.md) - Quote export to Excel/PDF
- [Quote Reference System](features/quote-reference-system.md) - Quote numbering and references

### 📋 Guides
- [Safe Merge Guide](guides/safe-merge-guide.md) - How to safely merge branches
- [Sensitive Files Guide](guides/sensitive-files-guide.md) - Managing secrets and config files

---

## 📁 Project Structure

```
fan-quoting-app/                       # Repository root
├── README.md                          # Project overview ⭐ START HERE
├── WORKFLOW_QUICK_REFERENCE.md       # Development commands
│
├── docs/                              # Project documentation (YOU ARE HERE)
│   ├── README.md                     # This file
│   │
│   ├── features/                      # Feature implementation docs
│   │   ├── dual-authentication.md
│   │   ├── export-functionality.md
│   │   └── quote-reference-system.md
│   │
│   ├── guides/                        # How-to guides
│   │   ├── safe-merge-guide.md
│   │   └── sensitive-files-guide.md
│   │
│   └── archive/                       # Historical documentation
│       ├── restructure-summary.md
│       └── gemini.md
│
├── deploy/                            # Deployment scripts & docs
│   ├── README.md                     # Deployment overview
│   ├── docs/                         # Deployment documentation
│   └── scripts/                      # Deployment scripts
│
├── api/                               # FastAPI backend
│   └── app/                          # Application code
│
├── ui/                                # Streamlit frontend
│   └── pages/                        # UI pages
│
└── database/                          # Database setup
    ├── init-scripts/                 # SQL initialization scripts
    └── data/                         # CSV data files
```

---

## 🔗 External Documentation

### Production URLs
- **Application**: https://quoting.airblowfans.org
- **API**: https://quoting-api-*.run.app
- **API Docs**: https://quoting-api-*.run.app/docs

### Google Cloud
- **GCP Console**: https://console.cloud.google.com
- **Project**: abf-fan-quoting-app
- **Region**: 

### Development
- **Local UI**: http://localhost:8501
- **Local API**: http://localhost:8080
- **Local API Docs**: http://localhost:8080/docs

---

## 📚 Documentation Index by Type

### Reference Documentation
| Document | Description | Location |
|----------|-------------|----------|
| Quote Data Schema | Complete JSONB structure definition | `../../Documentation/quote_data_schema_v3.md` |
| API Documentation | Interactive FastAPI docs | http://localhost:8080/docs |
| Deployment Scripts | Script reference and usage | `../deploy/README.md` |

### Implementation Guides
| Guide | Description | Location |
|-------|-------------|----------|
| Dual Authentication | Email + API key system | `features/dual-authentication.md` |
| Export Functionality | Quote export implementation | `features/export-functionality.md` |
| Quote Reference System | Reference numbering system | `features/quote-reference-system.md` |

### Development Guides
| Guide | Description | Location |
|-------|-------------|----------|
| Workflow Quick Reference | Common dev commands | `../WORKFLOW_QUICK_REFERENCE.md` |
| Safe Merge Guide | Branch merging best practices | `guides/safe-merge-guide.md` |
| Sensitive Files Guide | Managing secrets | `guides/sensitive-files-guide.md` |

### Deployment Guides
| Guide | Description | Location |
|-------|-------------|----------|
| Quick Start | 1-hour deployment | `../deploy/docs/QUICK_START.md` |
| Complete Deployment Guide | Full instructions | `../deploy/docs/DEPLOYMENT_GUIDE.md` |
| Configuration Guide | Credentials management | `../deploy/docs/CONFIGURATION_GUIDE.md` |
| Database Connection | Connect to Cloud SQL | `../deploy/docs/DATABASE_CONNECTION_GUIDE.md` |

---

## 🔄 Common Workflows

### Local Development
```bash
# Start services
docker-compose up

# Access UI: http://localhost:8501
# Access API: http://localhost:8080/docs
```
📖 **See**: [Workflow Quick Reference](../WORKFLOW_QUICK_REFERENCE.md)

### Deploy Changes
```bash
# Deploy API
python deploy/scripts/3_deploy_api.py

# Deploy UI (follow instructions)
python deploy/scripts/4_deploy_ui.py
```
📖 **See**: [Deployment Guide](../deploy/docs/DEPLOYMENT_GUIDE.md)

### Working with Features
```bash
# Create feature branch
git checkout -b feature/your-feature

# Develop and test locally
docker-compose up --build

# Deploy when ready
python deploy/scripts/3_deploy_api.py
```
📖 **See**: [Workflow Quick Reference](../WORKFLOW_QUICK_REFERENCE.md)

---

## 📝 Documentation Standards

All documentation in this project follows these conventions:

1. **Title**: Clear, descriptive title with emoji
2. **Purpose**: Brief description of what the doc covers
3. **Last Updated**: Date of last significant update
4. **Related Docs**: Links to related documentation
5. **Navigation**: Clear table of contents for longer docs

---

## 🆕 Recent Changes

### October 31, 2025
- Reorganized project documentation into `docs/` folder
- Created feature and guide subfolders
- Archived historical documentation
- Created documentation indexes
- Updated cross-references

---

## 💡 Tips for Finding Documentation

**Use the search function** in VS Code to find specific topics across all documentation:
- Press `Ctrl+Shift+F` to search in all files
- Search for keywords like "authentication", "export", "deployment"

**Start with these docs** depending on your task:
- New to the project? → [Main README](../README.md)
- Developing? → [Workflow Quick Reference](../WORKFLOW_QUICK_REFERENCE.md)
- Deploying? → [Deployment Docs](../deploy/docs/README.md)
- Understanding data? → [Quote Data Schema](../../Documentation/quote_data_schema_v3.md)

---

**Last Updated**: October 31, 2025  
**Maintained By**: Development Team
