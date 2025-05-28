@echo off
title CVLatex Production Server
color 0A

echo.
echo ========================================
echo    CVLatex Production Server
echo ========================================
echo.

cd /d "D:\CVLatex"

echo Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo Checking dependencies...
pip show flask > nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo Starting CVLatex Production Server...
echo.
echo Options:
echo [1] Flask Development Server (python app.py)
echo [2] Flask Production Server (python start_production.py) 
echo [3] Gunicorn Production Server (gunicorn)
echo [4] Exit
echo.

set /p choice="Choose option (1-4): "

if "%choice%"=="1" (
    echo Starting Flask Development Server...
    python app.py
) else if "%choice%"=="2" (
    echo Starting Flask Production Server...
    python start_production.py
) else if "%choice%"=="3" (
    echo Starting Gunicorn Production Server...
    gunicorn app:app --bind 0.0.0.0:8000 --workers 2 --timeout 120 --access-logfile access.log --error-logfile error.log
) else if "%choice%"=="4" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice!
    pause
    goto :EOF
)

echo.
echo Server stopped.
pause 