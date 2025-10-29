# Development Workflow Quick Reference

## Table of Contents
- [🚀 Common Commands](#-common-commands)
  - [Local Development (Docker)](#local-development-docker)
  - [Access URLs](#access-urls)
- [🌿 Git Workflow](#-git-workflow)
  - [Create Feature Branch](#create-feature-branch)
  - [Work on Feature](#work-on-feature)
  - [Merge to Main](#merge-to-main)
  - [Common Branch Names](#common-branch-names)
- [🚢 Deployment](#-deployment)
  - [Update Database Schema](#update-database-schema)
  - [Deploy API](#deploy-api)
  - [Deploy UI](#deploy-ui)
  - [Full Deployment](#full-deployment-after-database-changes)
- [👤 User Management](#-user-management)
  - [Generate Password Hash](#generate-password-hash)
  - [Add User to Database](#add-user-to-database-sql)
  - [User Roles](#user-roles)
- [🧪 Testing](#-testing)
- [🔍 Troubleshooting](#-troubleshooting)
  - [Docker Issues](#docker-issues)
  - [Git Issues](#git-issues)
  - [Database Issues](#database-issues)
- [📝 Development Checklist](#-development-checklist)
  - [Before Starting New Feature](#before-starting-new-feature)
  - [During Development](#during-development)
  - [Before Deploying](#before-deploying)
  - [Deployment Steps](#deployment-steps)
  - [After Deployment](#after-deployment)
- [🔗 Quick Links](#-quick-links)
  - [Documentation](#documentation)
  - [Production URLs](#production-urls)
  - [Development Tools](#development-tools)
- [💡 Tips & Best Practices](#-tips--best-practices)

---

## 🚀 Common Commands

### Local Development (Docker)
```bash
# Start everything
docker-compose up

# Rebuild after code/schema changes
docker-compose up --build

# Fresh database (removes all data)
docker-compose down -v
docker-compose up

# View logs
docker-compose logs -f api    # API logs
docker-compose logs -f ui     # UI logs
docker-compose logs -f db     # Database logs

# Stop all services
docker-compose down
```

### Access URLs
* **UI**: http://localhost:8501
* **API**: http://localhost:8080
* **API Docs**: http://localhost:8080/docs
* **Database**: localhost:5433 (DBeaver/pgAdmin)

---

## 🌿 Git Workflow

### Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### Work on Feature
```bash
# Make changes
git add .
git commit -m "Descriptive message"
git push origin feature/your-feature-name
```

### Merge to Main
```bash
git checkout main
git merge feature/your-feature-name
git push origin main
```

### Common Branch Names
* `feature/feature-name` - New features
* `bugfix/issue-description` - Bug fixes
* `hotfix/critical-fix` - Urgent production fixes
* `refactor/improvement` - Code improvements

---

## 🚢 Deployment

### Update Database Schema
```bash
python deploy/2_init_database.py
```

### Deploy API
```bash
python deploy/3_deploy_api.py
```

### Deploy UI
```bash
python deploy/4_deploy_ui.py
```

### Full Deployment (after database changes)
```bash
python deploy/2_init_database.py
python deploy/3_deploy_api.py
python deploy/4_deploy_ui.py
```

---

## 👤 User Management

### Generate Password Hash
```bash
python utils/hash_password.py
# Enter password when prompted
```

### Add User to Database (SQL)
```sql
INSERT INTO users (username, email, password_hash, full_name, phone, department, role)
VALUES ('username', 'user@example.com', '<bcrypt_hash>', 'Full Name', '+27 XX XXX XXXX', 'Engineering', 'user');
```

### User Roles
* `admin` - Full access
* `engineer` - Create/modify quotes
* `sales` - Create quotes, reports
* `user` - Standard access
* `guest` - Read-only

---

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_calculation_engine.py
```

### Run Tests with Coverage
```bash
pytest --cov=app tests/
```

---

## 🔍 Troubleshooting

### Docker Issues

**Containers won't start:**
```bash
docker-compose down
docker-compose up --build
```

**Database connection errors:**
```bash
# Check if DB is running
docker ps

# View DB logs
docker-compose logs db

# Rebuild DB
docker-compose down -v
docker-compose up
```

**Port already in use:**
```bash
# Check what's using the port
netstat -ano | findstr :8501
netstat -ano | findstr :8000
netstat -ano | findstr :5433

# Kill process or change port in docker-compose.yml
```

### Git Issues

**Merge conflicts:**
```bash
# See conflicted files
git status

# Manually resolve conflicts in files
# Then:
git add .
git commit -m "Resolve merge conflicts"
```

**Undo last commit (keep changes):**
```bash
git reset --soft HEAD~1
```

**Discard all local changes:**
```bash
git reset --hard HEAD
git clean -fd
```

### Database Issues

**Reset local database:**
```bash
docker-compose down -v
docker-compose up
```

**Connect to database:**
```bash
# Using psql
docker exec -it quoting_db_dev psql -U postgres -d fan_quoting_db

# Using DBeaver/pgAdmin
# Host: localhost
# Port: 5433
# Database: fan_quoting_db
# User: postgres
# Password: (from .env file)
```

---

## 📝 Development Checklist

### Before Starting New Feature
- [ ] Create feature branch: `git checkout -b feature/name`
- [ ] Pull latest main: `git pull origin main`
- [ ] Start Docker: `docker-compose up`

### During Development
- [ ] Test locally in Docker
- [ ] Write/update tests
- [ ] Update documentation if needed
- [ ] Commit frequently with clear messages

### Before Deploying
- [ ] All tests pass: `pytest`
- [ ] No lint errors
- [ ] Feature tested locally
- [ ] Database schema updated if needed
- [ ] README.md updated if needed

### Deployment Steps
- [ ] Commit and push all changes
- [ ] Update database: `python deploy/2_init_database.py`
- [ ] Deploy API: `python deploy/3_deploy_api.py`
- [ ] Deploy UI: `python deploy/4_deploy_ui.py`
- [ ] Test production deployment
- [ ] Merge feature branch to main

### After Deployment
- [ ] Verify production works
- [ ] Check logs for errors
- [ ] Update Streamlit Cloud access list if needed
- [ ] Document any manual steps taken

---

## 🔗 Quick Links

### Documentation
* Main README: `README.md`
* Schema Docs: `../Documentation/quote_data_schema_v3.md`
* Deployment Guide: `deploy/docs/DEPLOYMENT_GUIDE.md`
* Auth Guide: `DUAL_AUTH_IMPLEMENTATION.md`

### Production URLs
* **API**: https://your-api.run.app
* **UI**: https://your-app.streamlit.app
* **API Docs**: https://your-api.run.app/docs

### Development Tools
* **Docker Dashboard**: Docker Desktop → Containers
* **Database Client**: DBeaver, pgAdmin, or psql
* **API Testing**: http://localhost:8000/docs (Swagger UI)
* **Git GUI**: GitHub Desktop, GitKraken, or command line

---

## 💡 Tips & Best Practices

### Docker
* Always use `docker-compose down -v` when changing database schema
* Use `--build` flag when Dockerfile or requirements change
* Check logs with `docker-compose logs -f <service>`

### Git
* Use descriptive branch names: `feature/user-authentication`
* Write clear commit messages: "Add user login with bcrypt"
* Commit often, push regularly
* Keep feature branches short-lived

### Database
* Test schema changes in Docker first
* Backup production before major migrations
* Use migrations for production (not drop/recreate)

### Testing
* Write tests for new features
* Run tests before committing
* Use pytest fixtures for test data

### Security
* Never commit secrets (already in .gitignore)
* Always hash passwords with bcrypt
* Review .gitignore before adding new files
* Use environment variables for sensitive config

---

**Last Updated**: October 29, 2025
