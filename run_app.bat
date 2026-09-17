@echo off
title YouTube Studio Suite - Local
echo ===================================================
echo   Starting YouTube Studio Suite (Local)...
echo ===================================================
echo.
cd /d "%~dp0"
python -m streamlit run app.py --server.port 8501
pause
