#!/usr/bin/env pwsh
# The Empathy Engine - Single Command Startup Script
# This script starts both backend and frontend servers

Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   THE EMPATHY ENGINE - STARTING...   ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝`n" -ForegroundColor Cyan

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Function to check if a port is in use
function Test-Port {
    param([int]$Port)
    $connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return $null -ne $connection
}

# Check if ports are already in use
if (Test-Port 8000) {
    Write-Host "⚠️  Port 8000 is already in use (Backend)" -ForegroundColor Yellow
    Write-Host "   Kill the process? (y/n): " -NoNewline
    $response = Read-Host
    if ($response -eq 'y') {
        $pid = (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Select-Object -First 1
        Stop-Process -Id $pid -Force
        Write-Host "✅ Killed process on port 8000" -ForegroundColor Green
        Start-Sleep -Seconds 2
    }
}

if (Test-Port 3000) {
    Write-Host "⚠️  Port 3000 is already in use (Frontend)" -ForegroundColor Yellow
    Write-Host "   Kill the process? (y/n): " -NoNewline
    $response = Read-Host
    if ($response -eq 'y') {
        $pid = (Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue).OwningProcess | Select-Object -First 1
        if ($pid) {
            Stop-Process -Id $pid -Force
            Write-Host "✅ Killed process on port 3000" -ForegroundColor Green
            Start-Sleep -Seconds 2
        }
    }
}

Write-Host "`n🚀 Starting Backend Server..." -ForegroundColor Yellow
$backendPath = Join-Path $projectRoot "backend"
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

# Start backend in new window
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$backendPath'; & '$pythonExe' main.py"
) -WindowStyle Normal

Write-Host "✅ Backend starting on http://localhost:8000" -ForegroundColor Green

# Wait for backend to be ready
Write-Host "`n⏳ Waiting for backend to be ready..." -ForegroundColor Yellow
$maxAttempts = 15
$attempt = 0
$backendReady = $false

while (-not $backendReady -and $attempt -lt $maxAttempts) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.status -eq "online") {
            $backendReady = $true
        }
    }
    catch {
        $attempt++
        Write-Host "." -NoNewline -ForegroundColor DarkGray
    }
}

if ($backendReady) {
    Write-Host "`n✅ Backend is ready!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Backend may still be starting..." -ForegroundColor Yellow
}

Write-Host "`n🚀 Starting Frontend Server..." -ForegroundColor Yellow
$frontendPath = Join-Path $projectRoot "frontend"

# Start frontend in new window
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$frontendPath'; npm run dev"
) -WindowStyle Normal

Write-Host "✅ Frontend starting on http://localhost:3000" -ForegroundColor Green

# Wait a moment for frontend to start
Start-Sleep -Seconds 3

Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║   ✅ SERVERS STARTED SUCCESSFULLY!   ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "🌐 Access your application:" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Frontend App:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:3000" -ForegroundColor Green -BackgroundColor DarkGreen
Write-Host "   Backend API:   " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host "   API Docs:      " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

Write-Host "💡 Tip: Keep the terminal windows open while using the app" -ForegroundColor Yellow
Write-Host "🛑 To stop: Close the terminal windows or press Ctrl+C in each" -ForegroundColor Yellow

# Ask if user wants to open browser
Write-Host "`nOpen frontend in browser? (y/n): " -NoNewline -ForegroundColor White
$openBrowser = Read-Host

if ($openBrowser -eq 'y') {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:3000"
    Write-Host "✅ Browser opened!" -ForegroundColor Green
}

Write-Host "`n🎉 Enjoy The Empathy Engine!" -ForegroundColor Magenta
Write-Host "Press any key to exit this window..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
