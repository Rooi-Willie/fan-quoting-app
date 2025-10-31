@echo off
REM Verify sensitive files before merging
REM This checks if your sensitive files exist and shows their status

echo ========================================
echo SENSITIVE FILES CHECK
echo ========================================
echo.

set MISSING=0
set FOUND=0

echo Checking for sensitive configuration files...
echo.

REM Check deploy/config.yaml
if exist "deploy\config.yaml" (
    echo [✓] deploy\config.yaml - FOUND
    set /a FOUND+=1
) else (
    echo [✗] deploy\config.yaml - MISSING
    set /a MISSING+=1
)

REM Check .env
if exist ".env" (
    echo [✓] .env - FOUND
    set /a FOUND+=1
) else (
    echo [✗] .env - MISSING
    set /a MISSING+=1
)

REM Check ui/.streamlit/secrets.toml
if exist "ui\.streamlit\secrets.toml" (
    echo [✓] ui\.streamlit\secrets.toml - FOUND
    set /a FOUND+=1
) else (
    echo [✗] ui\.streamlit\secrets.toml - MISSING
    set /a MISSING+=1
)

REM Check cloud_sql_proxy.exe
if exist "deploy\cloud_sql_proxy.exe" (
    echo [✓] deploy\cloud_sql_proxy.exe - FOUND
    set /a FOUND+=1
) else (
    echo [✗] deploy\cloud_sql_proxy.exe - MISSING (will be downloaded if needed)
)

echo.
echo ========================================
echo SUMMARY
echo ========================================
echo Files found: %FOUND%
echo Files missing: %MISSING%
echo.

if %MISSING% GTR 0 (
    echo ⚠️  WARNING: Some sensitive files are missing!
    echo These files are NOT in git and need to be backed up separately.
) else (
    echo ✓ All critical files present
)

echo.
echo ========================================
echo GIT IGNORE STATUS
echo ========================================
echo.
echo Checking which files are gitignored...
echo.

git check-ignore -v deploy\config.yaml .env ui\.streamlit\secrets.toml 2>nul
if errorlevel 1 (
    echo ⚠️  Some files may NOT be gitignored!
    echo Run: git status
)

echo.
echo ========================================
echo RECOMMENDATIONS
echo ========================================
echo.
echo Before merging branches:
echo   1. Run: backup_sensitive.bat
echo   2. Verify backup was created
echo   3. Perform your git operations
echo   4. Restore if needed from backup folder
echo.
echo Git will NOT delete gitignored files when switching branches,
echo but it's good practice to have backups!
echo.

pause
