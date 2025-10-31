# 🔄 Quick Migration Guide

**If you're seeing "file not found" errors, this guide is for you!**

---

## ⚠️ What Changed?

On October 31, 2025, we reorganized the project structure for better organization and maintainability.

---

## 🚀 Deployment Scripts

### Old Paths ❌
```bash
python deploy/1_setup_gcp.py
python deploy/2_init_database.py
python deploy/3_deploy_api.py
python deploy/4_deploy_ui.py
python deploy/5_monitor.py
python deploy/6_manage_resources.py
python deploy/cleanup.py
```

### New Paths ✅
```bash
python deploy/scripts/1_setup_gcp.py
python deploy/scripts/2_init_database.py
python deploy/scripts/3_deploy_api.py
python deploy/scripts/4_deploy_ui.py
python deploy/scripts/5_monitor.py
python deploy/scripts/6_manage_resources.py
python deploy/scripts/cleanup.py
```

**Quick Fix**: Add `/scripts/` after `deploy/`

---

## 📚 Documentation

### Old Locations ❌
```
DUAL_AUTH_IMPLEMENTATION.md
EXPORT_IMPLEMENTATION.md
QUOTE_REFERENCE_SYSTEM.md
SAFE_MERGE_GUIDE.md
SENSITIVE_FILES_GUIDE.md
deploy/RESTRUCTURE_COMPLETE.md
deploy/TIMEZONE_DEPLOYMENT.md
```

### New Locations ✅
```
docs/features/dual-authentication.md
docs/features/export-functionality.md
docs/features/quote-reference-system.md
docs/guides/safe-merge-guide.md
docs/guides/sensitive-files-guide.md
deploy/docs/archive/RESTRUCTURE_COMPLETE.md
deploy/docs/archive/TIMEZONE_DEPLOYMENT.md
```

**Navigation**: Start with `docs/README.md` for the complete index

---

## 🔧 Cloud SQL Proxy

### Old Location ❌
```
deploy/cloud_sql_proxy.exe
```

### New Location ✅
```
deploy/bin/cloud_sql_proxy.exe
```

---

## 📖 Finding Documentation

**Lost?** Use these entry points:

1. **Main project**: `README.md`
2. **All documentation**: `docs/README.md`
3. **Deployment**: `deploy/docs/README.md`
4. **Quick commands**: `WORKFLOW_QUICK_REFERENCE.md`

---

## 🛠️ Update Your Scripts/Shortcuts

If you have any external scripts or shortcuts that reference the old paths:

**Find and Replace:**
- `deploy/1_` → `deploy/scripts/1_`
- `deploy/2_` → `deploy/scripts/2_`
- `deploy/3_` → `deploy/scripts/3_`
- `deploy/4_` → `deploy/scripts/4_`
- `deploy/5_` → `deploy/scripts/5_`
- `deploy/6_` → `deploy/scripts/6_`
- `deploy/cleanup.py` → `deploy/scripts/cleanup.py`
- `deploy/test_deployment.py` → `deploy/scripts/test_deployment.py`

---

## 📞 Still Lost?

Check the [Reorganization Summary](REORGANIZATION_COMPLETE.md) for complete details on what moved where.

---

**Date**: October 31, 2025
