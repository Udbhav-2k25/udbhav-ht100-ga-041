# PowerShell version of demo script for Windows

# ============================================================================
# The Empathy Engine - Demo Script (Windows)
# Tests the /analyze endpoint with sample conversation
# ============================================================================

Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   THE EMPATHY ENGINE - API Demo       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Configuration
$API_URL = "http://localhost:8000"
$DEMO_FILE = "demo/conversation.json"

# Check if backend is running
Write-Host "[1/3] Checking if backend is running..." -ForegroundColor Yellow
try {
    $null = Invoke-WebRequest -Uri "$API_URL/" -Method Get -TimeoutSec 2 -UseBasicParsing
    Write-Host "✓ Backend is online" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend not running. Start it with:" -ForegroundColor Red
    Write-Host "   cd backend" -ForegroundColor Red
    Write-Host "   python main.py" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test /analyze endpoint
Write-Host "[2/3] Testing POST /analyze endpoint..." -ForegroundColor Yellow
Write-Host ""

$demoData = Get-Content $DEMO_FILE -Raw
$response = Invoke-RestMethod -Uri "$API_URL/analyze" -Method Post -Body $demoData -ContentType "application/json"

$response | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "✓ Analysis complete" -ForegroundColor Green
Write-Host ""

# Test /summary endpoint
Write-Host "[3/3] Testing POST /summary endpoint..." -ForegroundColor Yellow
Write-Host ""

$summaryData = @{session_id = "demo1"} | ConvertTo-Json
$summary = Invoke-RestMethod -Uri "$API_URL/summary" -Method Post -Body $summaryData -ContentType "application/json"

$summary | ConvertTo-Json -Depth 10

Write-Host ""
Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Demo Complete!                       ║" -ForegroundColor Cyan
Write-Host "║   Check the emotion timeline above     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
