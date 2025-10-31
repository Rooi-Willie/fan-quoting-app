# Safe Merge & Deployment Guide

## 🎯 Goal
Merge `feature/user-authentication` to `main` and deploy to GCP without losing sensitive files.

## ⚠️ Important Understanding

**Git does NOT touch gitignored files when switching branches.**

The files that are gitignored (`.env`, `config.yaml`, `secrets.toml`) exist ONLY in your working directory. Git doesn't track them, so:
- ✅ They WON'T be deleted when you switch branches
- ✅ They WON'T be deleted when you merge
- ⚠️ They COULD be accidentally overwritten if you're not careful

## 📋 Safe Merge Process

### Step 1: Verify Everything Works on Feature Branch
```bash
# Make sure you're on feature branch
git branch

# Expected: * feature/user-authentication
```

### Step 2: Check Sensitive Files
```bash
# Run verification script
check_sensitive.bat
```

**Expected output:** All critical files should show `[✓] FOUND`

### Step 3: Backup Sensitive Files (Safety Net)
```bash
# Create timestamped backup
backup_sensitive.bat
```

**Result:** Creates folder like `backup_sensitive_20251031_143022` with all sensitive files

### Step 4: Verify Backup
```bash
dir backup_sensitive_*
```

**Expected:** You should see your backup folder with files inside

### Step 5: Commit All Changes on Feature Branch
```bash
# Make sure everything is committed
git status

# If there are uncommitted changes:
git add .
git commit -m "Final changes before merge - timezone updates and deployment fixes"
```

### Step 6: Switch to Main Branch
```bash
git checkout main
```

**What happens:**
- ✅ Git switches your code files
- ✅ Gitignored files stay exactly where they are (NOT touched)
- ⚠️ If main branch has different code, you'll see those changes

### Step 7: Verify Sensitive Files Still Exist
```bash
# Quick check
check_sensitive.bat
```

**Expected:** All files should still show `[✓] FOUND`

### Step 8: Merge Feature Branch
```bash
git merge feature/user-authentication
```

**What happens:**
- ✅ Code changes merge into main
- ✅ Gitignored files are NOT touched
- ⚠️ Resolve any merge conflicts if they appear

### Step 9: Final Verification
```bash
# Check everything again
check_sensitive.bat

# Check git status
git status
```

**Expected:** 
- All sensitive files present
- No uncommitted changes (clean merge)

### Step 10: Push to Remote
```bash
git push origin main
```

## 🚀 Deploy to GCP

Now you can deploy from the `main` branch:

```bash
# Step 1: Setup GCP resources
python deploy/1_setup_gcp.py

# Step 2: Initialize database (with timezone fixes!)
python deploy/2_init_database.py

# Step 3: Deploy API
python deploy/3_deploy_api.py

# Step 4: Deploy UI
python deploy/4_deploy_ui.py
```

## 🆘 If Something Goes Wrong

### Restore from Backup
```bash
cd backup_sensitive_YYYYMMDD_HHMMSS
restore_this_backup.bat
```

### Or manually copy:
```bash
# From backup folder to project:
copy config.yaml ..\..\..\deploy\
copy .env ..\..\..
copy secrets.toml ..\..\..\ui\.streamlit\
```

## 📝 Why This Works

1. **Gitignored files are NOT in git**
   - Git never sees them
   - Git never tracks changes to them
   - Git never deletes them when switching branches

2. **They exist in your file system only**
   - They stay in place during branch operations
   - They could only be lost if YOU delete them manually

3. **Backup is insurance**
   - Even though git won't touch them, backups protect against human error
   - If you accidentally delete something, you can restore it

## ✅ Quick Checklist

Before merging:
- [ ] Run `check_sensitive.bat` - verify all files exist
- [ ] Run `backup_sensitive.bat` - create backup
- [ ] Verify backup was created successfully
- [ ] Commit all changes on feature branch
- [ ] Switch to main: `git checkout main`
- [ ] Run `check_sensitive.bat` again - files should still be there
- [ ] Merge: `git merge feature/user-authentication`
- [ ] Run `check_sensitive.bat` final check
- [ ] Deploy to GCP

## 🎓 Understanding the Previous Issue

**What probably happened before:**
- You might have manually deleted files thinking you needed to "clean up"
- Or you ran `git clean` which CAN delete untracked files
- Or you recreated the directory structure

**What did NOT happen:**
- Git did NOT delete your files during branch operations
- Git does NOT touch gitignored files

**Prevention:**
- Never run `git clean -fd` (force delete untracked files)
- Always use `git clean -n` (dry run) first to see what would be deleted
- Keep backups of sensitive files

---

**Remember:** Git ignores gitignored files completely. They're safe during normal git operations! 🎯
