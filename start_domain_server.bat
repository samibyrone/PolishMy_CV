@echo off
title CVLatex - cvlatex.zapto.org
color 0B
cls

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                     CVLatex Domain Server                   ║
echo ║                                                              ║
echo ║  🌐 Domain: cvlatex.zapto.org                               ║
echo ║  🚀 Starting production server with domain support...       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

cd /d "D:\CVLatex"

echo [1/4] Checking environment...
python --version
if errorlevel 1 (
    echo ❌ ERROR: Python not found!
    pause
    exit /b 1
)

echo ✅ Python: OK
echo.

echo [2/4] Checking LaTeX...
python -c "import shutil; print('✅ pdflatex available:' if shutil.which('pdflatex') else '❌ pdflatex missing:', shutil.which('pdflatex'))"
echo.

echo [3/4] Starting CVLatex Production Server...
echo 📍 Local URL: http://localhost:8000
echo 🌐 Domain URL: https://cvlatex.zapto.org (after tunnel setup)
echo.

start "CVLatex Production Server" python start_production.py

timeout /t 5

echo [4/4] Setup Options:
echo.
echo Choose your setup method:
echo [1] Start Cloudflare Tunnel (Recommended - Free SSL)
echo [2] Instructions for Port Forwarding
echo [3] Just run locally (localhost:8000)
echo [4] Exit
echo.

set /p choice="Choose option (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🔧 Starting Cloudflare Tunnel...
    echo.
    echo 📋 Make sure you have:
    echo    1. Installed cloudflared.exe
    echo    2. Created tunnel: cloudflared tunnel create cvlatex
    echo    3. Updated cloudflare-tunnel.yml with your tunnel ID
    echo.
    echo Starting tunnel now...
    start "Cloudflare Tunnel" cloudflared tunnel run cvlatex
    echo.
    echo ✅ CVLatex is now running at:
    echo 🌐 Main Site: https://cvlatex.zapto.org
    echo 📊 Admin Panel: https://admin.cvlatex.zapto.org
    echo 🔧 API: https://api.cvlatex.zapto.org
    echo 💻 Local: http://localhost:8000
    
) else if "%choice%"=="2" (
    echo.
    echo 📋 Port Forwarding Setup Instructions:
    echo.
    echo 1. Open your router admin panel
    echo 2. Find Port Forwarding settings
    echo 3. Add new rule:
    echo    - External Port: 80 or 8000
    echo    - Internal Port: 8000
    echo    - Internal IP: Your PC IP (run: ipconfig)
    echo    - Protocol: TCP
    echo 4. Save settings
    echo 5. Update cvlatex.zapto.org DNS to point to your public IP
    echo.
    echo Your site will be at: http://cvlatex.zapto.org:8000
    
) else if "%choice%"=="3" (
    echo.
    echo ✅ CVLatex running locally at:
    echo 💻 http://localhost:8000
    echo.
    echo To make it public, use option 1 or 2 above.
    
) else if "%choice%"=="4" (
    echo.
    echo 🛑 Stopping services...
    taskkill /F /IM python.exe >nul 2>&1
    taskkill /F /IM cloudflared.exe >nul 2>&1
    echo ✅ Services stopped. Goodbye!
    exit /b 0
    
) else (
    echo ❌ Invalid choice!
    timeout /t 3
    goto choice_menu
)

echo.
echo 📋 Useful Commands:
echo    Monitor: python monitor.py --status
echo    Logs: python monitor.py
echo    Test: curl http://localhost:8000
echo.
echo 🔗 Documentation: See DOMAIN_SETUP_GUIDE.md for detailed setup
echo.
echo Press any key to stop all services...
pause

:choice_menu
echo.
echo 🛑 Stopping services...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM cloudflared.exe >nul 2>&1
echo ✅ All services stopped.
echo.
echo Thank you for using CVLatex! 👋
pause 