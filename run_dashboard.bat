@echo off
title FatigueLab - Adversarial Prompt Fatigue Tester
echo ============================================================
echo   Starting FatigueLab Dashboard...
echo   Close this window when you want to stop the server.
echo ============================================================
echo.
python -m streamlit run dashboard.py
pause
