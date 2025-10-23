@echo off
REM Quick config switcher for Windows
REM Usage: config-dev.bat   or   config-prod.bat

cd /d "%~dp0"
python switch_config.py prod
echo.
echo Restart Streamlit for changes to take effect.
pause
