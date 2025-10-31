# 🔐 Managing Sensitive Configuration Files

This guide explains how to protect sensitive files from being lost during Git operations.

## The Problem

When switching branches, Git may delete untracked files (files in `.gitignore`). This can cause you to lose:
- `ui/.streamlit/secrets.toml` - API credentials
- `deploy/config.yaml` - Database passwords and deployment settings

## The Solution: Template Files

We use **template files** that ARE committed to Git, which you copy to create your actual config files.

### Template Files (✅ Safe to commit)
- `ui/.streamlit/secrets.toml.template`
- `deploy/config.yaml.template`

### Actual Files (❌ Never committed - in .gitignore)
- `ui/.streamlit/secrets.toml`
- `deploy/config.yaml`

---

## 🚀 Quick Start

### First Time Setup

```bash
# 1. Copy the template files
copy ui\.streamlit\secrets.toml.template ui\.streamlit\secrets.toml
copy deploy\config.yaml.template deploy\config.yaml

# 2. Edit the actual files with your values
# - secrets.toml: Set your API_BASE_URL and API_KEY
# - config.yaml: Set strong passwords for database

# 3. Verify they're ignored by Git
git status  # Should NOT show secrets.toml or config.yaml
```

### If You Lose the Files

```bash
# Just recreate from templates
copy ui\.streamlit\secrets.toml.template ui\.streamlit\secrets.toml
copy deploy\config.yaml.template deploy\config.yaml

# Then fill in your actual values again
```

---

## 🛡️ Best Practices

### 1. **Always Keep Backups**
- Store passwords in a password manager (e.g., 1Password, LastPass, Bitwarden)
- Keep a backup copy in a secure location (e.g., OneDrive, encrypted folder)

### 2. **Before Switching Branches**
```bash
# Option A: Stash your untracked files
git stash --include-untracked

# Switch branches
git checkout main

# Restore files
git stash pop
```

```bash
# Option B: Just keep a backup
copy ui\.streamlit\secrets.toml ui\.streamlit\secrets.toml.backup
copy deploy\config.yaml deploy\config.yaml.backup

# Then restore after branch switch if needed
```

### 3. **Verify .gitignore Protection**
```bash
# Check if files are properly ignored
git check-ignore -v ui/.streamlit/secrets.toml
git check-ignore -v deploy/config.yaml

# Both should show they're ignored
```

### 4. **Never Commit Sensitive Files**
```bash
# If you accidentally stage them
git reset HEAD ui/.streamlit/secrets.toml
git reset HEAD deploy/config.yaml

# Check what's staged before committing
git status
```

---

## 📋 What's Protected

### Files in .gitignore:
```
# Streamlit secrets
ui/.streamlit/secrets.toml
.streamlit/secrets.toml

# Deployment secrets
deploy/config.yaml
deploy/cloud_sql_proxy.exe
deploy/cloud_sql_proxy
```

### Files Safe to Commit:
```
# Templates (with placeholder values)
ui/.streamlit/secrets.toml.template
deploy/config.yaml.template

# Documentation
ui/.streamlit/README.md
deploy/docs/*.md
```

---

## 🔍 Troubleshooting

### "Secrets file not found" error
```bash
# Copy from template
copy ui\.streamlit\secrets.toml.template ui\.streamlit\secrets.toml
```

### Files keep getting deleted when switching branches
```bash
# Use git stash before switching
git stash --include-untracked
git checkout other-branch
git stash pop
```

### Accidentally committed a secret
```bash
# Remove from Git history (DANGEROUS - do this carefully)
git rm --cached ui/.streamlit/secrets.toml
git rm --cached deploy/config.yaml
git commit -m "Remove sensitive files from Git"

# Then make sure they're in .gitignore
# And consider rotating your passwords/API keys!
```

### Want to sync configs across branches
```bash
# Copy files before switching
copy ui\.streamlit\secrets.toml %TEMP%\secrets.toml
copy deploy\config.yaml %TEMP%\config.yaml

# Switch branch
git checkout other-branch

# Restore files
copy %TEMP%\secrets.toml ui\.streamlit\secrets.toml
copy %TEMP%\config.yaml deploy\config.yaml
```

---

## 📚 Additional Resources

- See `deploy/docs/GITIGNORE_GUIDE.md` for detailed .gitignore documentation
- See `ui/.streamlit/README.md` for Streamlit config management
- See `deploy/docs/DEPLOYMENT_GUIDE.md` for deployment instructions

---

## ✅ Quick Checklist

Before committing:
- [ ] `secrets.toml` is NOT in `git status`
- [ ] `config.yaml` is NOT in `git status`
- [ ] `.template` files ARE in `git status` (first time only)
- [ ] Passwords are backed up in password manager
- [ ] `.gitignore` contains sensitive file paths

You're protected! 🛡️
