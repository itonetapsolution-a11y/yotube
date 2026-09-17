@echo off
title YouTube Studio Suite - Live Public Server
echo =========================================================
echo    Starting YouTube Studio Suite with Live Public URL...
echo =========================================================
echo.
cd /d "%~dp0"

echo 1. Starting Streamlit Suite...
start /b python -m streamlit run app.py --server.headless true --server.port 8501

timeout /t 3 /nobreak >nul

echo 2. Generating Live Public HTTPS Link...
echo.
echo =========================================================
echo  Open the URL shown below on any Mobile, Tablet, or PC:
echo =========================================================
echo.
cloudflared.exe tunnel --url http://127.0.0.1:8501
pause
