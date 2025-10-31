@echo off
REM Safe merge helper - automates the backup and verification process

echo ========================================
echo SAFE MERGE HELPER
echo ========================================
echo.
echo This script will help you safely merge branches
echo while protecting your sensitive configuration files.
echo.

REM Step 1: Check current branch
echo [1/7] Checking current branch...
git branch --show-current > temp_branch.txt
set /p CURRENT_BRANCH=<temp_branch.txt
del temp_branch.txt
echo Current branch: %CURRENT_BRANCH%
echo.

REM Step 2: Verify sensitive files exist
echo [2/7] Verifying sensitive files exist...
call check_sensitive.bat
echo.

echo Press any key to continue with backup, or Ctrl+C to cancel...
pause >nul

REM Step 3: Create backup
echo [3/7] Creating backup...
call backup_sensitive.bat
echo.

REM Step 4: Show uncommitted changes
echo [4/7] Checking for uncommitted changes...
git status --short
echo.

choice /C YN /M "Do you want to commit all changes before merging"
if errorlevel 2 goto skip_commit
if errorlevel 1 goto do_commit

:do_commit
echo.
set /p COMMIT_MSG="Enter commit message: "
git add .
git commit -m "%COMMIT_MSG%"
echo.

:skip_commit
echo [5/7] Ready to merge!
echo.
echo Current branch: %CURRENT_BRANCH%
echo.
set /p TARGET_BRANCH="Enter target branch to merge INTO (e.g., main): "
echo.

echo Summary:
echo - Current branch: %CURRENT_BRANCH%
echo - Will switch to: %TARGET_BRANCH%
echo - Will merge: %CURRENT_BRANCH% into %TARGET_BRANCH%
echo - Backup created: YES
echo.

choice /C YN /M "Proceed with merge"
if errorlevel 2 goto cancelled
if errorlevel 1 goto proceed

:proceed
echo.
echo [6/7] Switching to %TARGET_BRANCH%...
git checkout %TARGET_BRANCH%
echo.

echo [7/7] Merging %CURRENT_BRANCH% into %TARGET_BRANCH%...
git merge %CURRENT_BRANCH%
echo.

if errorlevel 1 (
    echo ❌ Merge had conflicts!
    echo Please resolve conflicts manually, then run:
    echo   git add .
    echo   git commit
) else (
    echo ✓ Merge successful!
)

echo.
echo Verifying sensitive files after merge...
call check_sensitive.bat

echo.
echo ========================================
echo MERGE COMPLETE
echo ========================================
echo.
echo Next steps:
echo 1. Verify everything works
echo 2. Push to remote: git push origin %TARGET_BRANCH%
echo 3. Deploy to GCP
echo.
goto end

:cancelled
echo.
echo ❌ Merge cancelled by user
echo Your backup is still available if you need it
echo.
goto end

:end
pause
