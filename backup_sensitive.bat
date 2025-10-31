@echo off
REM Backup sensitive files before branch operations
REM Run this before switching branches or merging

echo Creating backup of sensitive files...

REM Create backup outside git folder with better timestamp format
REM Get date in YYYYMMDD format
for /f "tokens=1-3 delims=/-" %%a in ('echo %date%') do (
    set DAY=%%a
    set MONTH=%%b
    set YEAR=%%c
)
set MYDATE=%YEAR%%MONTH%%DAY%

REM Get time in HHMM format
set HOUR=%time:~0,2%
set HOUR=%HOUR: =0%
set MINUTE=%time:~3,2%
set MYTIME=%HOUR%%MINUTE%

set BACKUP_DIR=..\backups\backup_sensitive_%MYDATE%_%MYTIME%

mkdir "%BACKUP_DIR%" 2>nul

echo Backing up to: %BACKUP_DIR%
echo.

REM Backup config files
if exist "deploy\config.yaml" (
    copy "deploy\config.yaml" "%BACKUP_DIR%\" >nul
    echo [✓] deploy\config.yaml
) else (
    echo [✗] deploy\config.yaml - not found
)

if exist ".env" (
    copy ".env" "%BACKUP_DIR%\" >nul
    echo [✓] .env
) else (
    echo [✗] .env - not found
)

REM Backup Streamlit secrets
if exist "ui\.streamlit\secrets.toml" (
    copy "ui\.streamlit\secrets.toml" "%BACKUP_DIR%\" >nul
    echo [✓] ui\.streamlit\secrets.toml
) else (
    echo [✗] ui\.streamlit\secrets.toml - not found
)

REM Backup any other sensitive files
if exist "deploy\cloud_sql_proxy.exe" (
    copy "deploy\cloud_sql_proxy.exe" "%BACKUP_DIR%\" >nul
    echo [✓] deploy\cloud_sql_proxy.exe
) else (
    echo [✗] deploy\cloud_sql_proxy.exe - not found (OK, will download if needed)
)

REM Create restore instructions file
echo RESTORE INSTRUCTIONS > "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo =================== >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo. >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo This backup was created on: %DATE% at %TIME% >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo. >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo FILE LOCATIONS: >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo --------------- >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo. >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo config.yaml         --^> fan-quoting-app\deploy\ >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo .env                --^> fan-quoting-app\ >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo secrets.toml        --^> fan-quoting-app\ui\.streamlit\ >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo cloud_sql_proxy.exe --^> fan-quoting-app\deploy\ >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo. >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo. >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo TO RESTORE: >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo ----------- >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo Option 1: Run the restore_this_backup.bat file in this folder >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo Option 2: Manually copy each file to its location shown above >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"
echo. >> "%BACKUP_DIR%\RESTORE_INSTRUCTIONS.txt"

echo.
echo ✓ Backup complete!
echo.
echo Files saved to: %BACKUP_DIR%
echo.
echo Restore instructions saved in: RESTORE_INSTRUCTIONS.txt
echo.

REM Create restore script
echo @echo off > "%BACKUP_DIR%\restore_this_backup.bat"
echo REM Restore sensitive files from backup >> "%BACKUP_DIR%\restore_this_backup.bat"
echo. >> "%BACKUP_DIR%\restore_this_backup.bat"
echo echo Restoring sensitive files... >> "%BACKUP_DIR%\restore_this_backup.bat"
echo echo. >> "%BACKUP_DIR%\restore_this_backup.bat"
echo. >> "%BACKUP_DIR%\restore_this_backup.bat"
echo if exist "config.yaml" ( >> "%BACKUP_DIR%\restore_this_backup.bat"
echo     copy "config.yaml" "..\..\fan-quoting-app\deploy\" ^>nul >> "%BACKUP_DIR%\restore_this_backup.bat"
echo     echo [✓] Restored config.yaml >> "%BACKUP_DIR%\restore_this_backup.bat"
echo ) >> "%BACKUP_DIR%\restore_this_backup.bat"
echo. >> "%BACKUP_DIR%\restore_this_backup.bat"
echo if exist ".env" ( >> "%BACKUP_DIR%\restore_this_backup.bat"
echo     copy ".env" "..\..\fan-quoting-app\" ^>nul >> "%BACKUP_DIR%\restore_this_backup.bat"
echo     echo [✓] Restored .env >> "%BACKUP_DIR%\restore_this_backup.bat"
echo ) >> "%BACKUP_DIR%\restore_this_backup.bat"
echo. >> "%BACKUP_DIR%\restore_this_backup.bat"
echo if exist "secrets.toml" ( >> "%BACKUP_DIR%\restore_this_backup.bat"
echo     copy "secrets.toml" "..\..\fan-quoting-app\ui\.streamlit\" ^>nul >> "%BACKUP_DIR%\restore_this_backup.bat"
echo     echo [✓] Restored secrets.toml >> "%BACKUP_DIR%\restore_this_backup.bat"
echo ) >> "%BACKUP_DIR%\restore_this_backup.bat"
echo. >> "%BACKUP_DIR%\restore_this_backup.bat"
echo if exist "cloud_sql_proxy.exe" ( >> "%BACKUP_DIR%\restore_this_backup.bat"
echo     copy "cloud_sql_proxy.exe" "..\..\fan-quoting-app\deploy\" ^>nul >> "%BACKUP_DIR%\restore_this_backup.bat"
echo     echo [✓] Restored cloud_sql_proxy.exe >> "%BACKUP_DIR%\restore_this_backup.bat"
echo ) >> "%BACKUP_DIR%\restore_this_backup.bat"
echo. >> "%BACKUP_DIR%\restore_this_backup.bat"
echo echo. >> "%BACKUP_DIR%\restore_this_backup.bat"
echo echo ✓ Restore complete! >> "%BACKUP_DIR%\restore_this_backup.bat"
echo pause >> "%BACKUP_DIR%\restore_this_backup.bat"

echo.
pause
