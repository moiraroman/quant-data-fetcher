@echo off
cd /d "%~dp0"
title Quant Data Fetcher

:: kill old processes on port 5050
for /f "tokens=5" %%P in ('netstat -ano ^| findstr ":5050" ^| findstr "LISTENING"') do (
    echo [STOP] Killing PID=%%P
    taskkill /F /PID %%P >nul 2>&1
)

timeout /t 1 /nobreak >nul

:: start
echo.
echo ============================================================
echo   Quant Data Fetcher
echo   Web : http://127.0.0.1:5050
echo ============================================================
echo.

python app.py
pause
