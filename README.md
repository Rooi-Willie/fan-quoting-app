# fan-quoting-app
Auxiliary axial fan quoting application.
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Rooi-Willie/fan-quoting-app)

## Quick Start

### Local Development (Docker)
```bash
docker-compose up          # Start all services
# UI: http://localhost:8501
# API: http://localhost:8080/docs
```

### Deploy to Production
```bash
python deploy/scripts/2_init_database.py  # Update database
python deploy/scripts/3_deploy_api.py     # Deploy API
python deploy/scripts/4_deploy_ui.py      # Deploy UI
```

### Create New Feature
```bash
git checkout -b feature/your-feature
# Develop, test, commit
git push origin feature/your-feature
# Merge to main when ready
```

## Documentation Index
* **Quick Reference**: `WORKFLOW_QUICK_REFERENCE.md` ⭐ **Start here for development!**
* **All Documentation**: `docs/README.md` - Complete documentation index
* **Schema**: `../Documentation/quote_data_schema_v3.md` - Quote data structure
* **Deployment**: `deploy/docs/README.md` - All deployment guides
* **Features**: `docs/features/` - Implementation documentation
* **Guides**: `docs/guides/` - How-to guides
* **API Reference**: http://localhost:8080/docs (when running locally)

## Overview
This repository contains a Streamlit UI and FastAPI backend for creating and managing axial fan quotations. Quote state is persisted as JSON (`quote_data`) alongside relational summary columns for efficient listing.

## Quote Data Schema
The application uses a modern, versioned schema (version = 3) for all quotes. Key characteristics:

### Schema Features
* **Logical Organization**: Structured into `meta`, `quote`, `specification`, `pricing`, `calculations`, and `context` sections
* **Separation of Concerns**: Clear distinction between technical specifications, pricing data, and computed results
* **Version Tracking**: `meta.version = 3` enables proper schema evolution

### Schema Sections
* **meta**: Version tracking, timestamps, and metadata
* **quote**: Basic quote identification and project information
* **specification**: Technical specifications (fan, components, motor, buyouts)
* **pricing**: All pricing data including overrides and final prices
* **calculations**: Server-computed results and aggregated totals
* **context**: Rates, settings, and audit information used in calculations

See full specification, examples, and API documentation:
* **Schema Documentation**: `../Documentation/quote_data_schema_v3.md`

## Architecture

### Frontend (Streamlit UI)
* **Multi-tab workflow**: Project info, fan configuration, motor selection, buyout items, review & save
* **Real-time calculations**: Component and pricing updates with immediate UI feedback
* **Session state management**: Schema-aware state handling with proper synchronization
* **Quote management**: Create, view, edit, and manage quote revisions

### Backend (FastAPI)
* **CRUD operations**: Complete quote lifecycle management
* **API endpoints**: Quote creation, schema validation, summary extraction
* **Summary extraction**: `_extract_summary_from_quote_data()` for database summary fields

### Database (PostgreSQL)
* **JSONB storage**: Efficient storage and querying of quote_data JSON
* **Summary columns**: Extracted fields for fast listing and filtering
* **Version tracking**: Schema version stored for proper handling
* **Revision management**: Complete quote history with immutable revisions

## Development Setup

### Prerequisites
* Python 3.8+
* Docker & Docker Compose
* PostgreSQL database (for production)
* Google Cloud SDK (for deployment)
* Required Python packages (see requirements.txt)

### Local Development with Docker (Recommended)

**Docker provides an isolated environment that mirrors production without touching live data.**

#### Starting the Development Environment
```bash
# Navigate to project root
cd fan-quoting-app

# Start all services (DB, API, UI)
docker-compose up

# Or rebuild after schema changes
docker-compose up --build

# Stop and remove volumes (fresh database)
docker-compose down -v
```

#### Access Points
* **UI**: http://localhost:8501
* **API**: http://localhost:8080
* **API Docs**: http://localhost:8080/docs
* **PostgreSQL**: localhost:5433 (for DBeaver/external tools)

#### Live Development
* Code changes auto-reload (volumes mounted)
* Database initialized with schema + sample data
* Separate test database on port 5431

### Alternative: Local Development with Cloud SQL

**Use Cloud SQL Proxy to test with production data (use with caution).**

```bash
# Terminal 1: Start Cloud SQL Proxy
.\cloud-sql-proxy.exe --port 5432 abf-fan-quoting-app:us-central1:fan-quoting-db

# Terminal 2: Run API locally
cd api
uvicorn app.main:app --reload --port 8080

# Terminal 3: Run UI locally
cd ui
streamlit run Login_Page.py
```

**⚠️ Warning**: This connects to production database. Use only for pre-deployment verification.

### Git Workflow (Feature Branch Strategy)

**Best practice for developing new features:**

```bash
# 1. Create feature branch
git checkout -b feature/feature-name

# 2. Develop and test locally (Docker)
docker-compose up --build
# Make changes, test, iterate

# 3. Commit changes
git add .
git commit -m "Descriptive commit message"

# 4. Push branch
git push origin feature/feature-name

# 5. Test with production data (optional)
# Stop Docker, use Cloud SQL Proxy
python deploy/scripts/_init_database.py  # Update Cloud SQL schema
# Test locally against Cloud SQL

# 6. Deploy to production
python deploy/scripts/_deploy_api.py
python deploy/scripts/_deploy_ui.py

# 7. Merge to main
git checkout main
git merge feature/feature-name
git push origin main
```

### Development Workflow Comparison

| Stage | Environment | Database | When to Use |
|-------|-------------|----------|-------------|
| **Development** | Docker (local) | Local PostgreSQL | Daily coding, testing, schema changes |
| **Pre-Deploy Testing** | Local + Cloud SQL Proxy | Cloud SQL | Verify with production data (optional) |
| **Production** | Cloud Run | Cloud SQL | Live system |

### Testing
* **Unit Tests**: Schema validation, calculations, and business logic
* **Integration Tests**: End-to-end quote workflow testing
* **Test Data**: Schema examples in `tests/test_data/`
* **Run Tests**: `pytest` or `pytest tests/`

## Recent Updates

### Security & Authentication (October 2025)
* ✅ **Dual Authentication System**: Streamlit OAuth + database authentication
* ✅ **User Management**: Role-based access control (admin, engineer, sales, user)
* ✅ **Quote Tracking**: User metadata in quote_data for audit trail
* ✅ **Password Security**: Bcrypt hashing for secure credential storage
* ✅ **User Profiles**: Extended user table with phone, department, job title

### Core Features
* ✅ **Modern Schema**: Complete implementation with logical section organization
* ✅ **UI Updates**: All components updated for proper schema paths
* ✅ **Testing**: Comprehensive test coverage for functionality
* ✅ **Documentation**: Complete schema specification

### Technical Improvements  
* ✅ **Session State Sync**: Fixed widget lag issues with proper state synchronization
* ✅ **Component Calculations**: Real-time updates with cache clearing and state management
* ✅ **Data Paths**: Clean schema paths throughout application
* ✅ **Error Handling**: Improved validation and error reporting

### Implementation Status
* ✅ **Core Implementation**: Schema fully implemented and tested
* ✅ **UI Updates**: All pages and components support current schema
* ✅ **API Support**: Backend handles quote operations transparently  
* ✅ **Testing**: Test suite covers all functionality
* ✅ **Documentation**: Complete documentation for usage

## Deployment

### Deployment to Google Cloud

**Prerequisites:**
* Google Cloud project configured
* Cloud SQL instance running
* Cloud Run services deployed
* Service accounts and API keys configured

**Deployment Scripts** (in `deploy/` directory):
```bash
# 1. Setup GCP resources (one-time)
python deploy/scripts/_setup_gcp.py

# 2. Initialize/update database schema
python deploy/scripts/_init_database.py

# 3. Deploy API to Cloud Run
python deploy/scripts/_deploy_api.py

# 4. Deploy UI to Cloud Run (or Streamlit Cloud)
python deploy/scripts/_deploy_ui.py

# 5. Monitor deployed services
python deploy/scripts/_monitor.py

# 6. Manage resources (start/stop/cleanup)
python deploy/scripts/_manage_resources.py
```

**See detailed deployment guide:** `deploy/docs/DEPLOYMENT_GUIDE.md`

### User Management

**Creating New Users:**

```bash
# Generate password hash
python utils/hash_password.py your_secure_password

# Add to database
INSERT INTO users (username, email, password_hash, full_name, phone, role)
VALUES ('username', 'user@example.com', '<hash>', 'Full Name', '+27 XX XXX XXXX', 'user');
```

**User Roles:**
* **admin**: Full access to all features including user management
* **engineer**: Create and modify quotes, access technical features
* **sales**: Create quotes, view reports, limited modifications
* **user**: Standard access, view-only for most features
* **guest**: Read-only access for demonstrations

**Streamlit Cloud Access Control:**
1. Go to Streamlit Cloud → App Settings → Sharing
2. Set "Who can view this app" to "Only specific people"
3. Add authorized email addresses (comma-separated)
4. Users authenticate via Google/GitHub OAuth, then login to app

**See authentication guide:** `DUAL_AUTH_IMPLEMENTATION.md`

## Future Enhancements

### Planned Features
* **Enhanced Audit Trail**: Extended context tracking and calculation history
* **Advanced Pricing Models**: Additional markup strategies and pricing rules
* **Workflow Management**: Status tracking and approval workflows  
* **Performance Optimization**: Caching improvements and calculation efficiency
* **Export Features**: PDF generation and data export capabilities

## License
Internal use (license details TBD).
