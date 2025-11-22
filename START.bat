@echo off
REM The Empathy Engine - Quick Starter
REM Double-click this file to start both servers

echo.
echo ╔════════════════════════════════════════╗
echo ║   THE EMPATHY ENGINE - STARTING...   ║
echo ╚════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo Starting Backend Server...
start "Empathy Engine - Backend" powershell -NoExit -Command "cd '%~dp0backend'; & '../.venv/Scripts/python.exe' main.py"

timeout /t 5 /nobreak >nul

echo Starting Frontend Server...
start "Empathy Engine - Frontend" powershell -NoExit -Command "cd '%~dp0frontend'; npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ╔════════════════════════════════════════╗
echo ║   ✅ SERVERS STARTED SUCCESSFULLY!   ║
echo ╚════════════════════════════════════════╝
echo.
echo 🌐 Access your application:
echo.
echo    Frontend App:  http://localhost:3000
echo    Backend API:   http://localhost:8000
echo    API Docs:      http://localhost:8000/docs
echo.
echo 💡 Keep the terminal windows open while using the app
echo 🛑 To stop: Close the terminal windows
echo.

choice /C YN /M "Open frontend in browser"
if errorlevel 2 goto :skip
if errorlevel 1 goto :open

:open
timeout /t 3 /nobreak >nul
start http://localhost:3000
echo ✅ Browser opened!

:skip
echo.
echo 🎉 Enjoy The Empathy Engine!
echo.
pause
