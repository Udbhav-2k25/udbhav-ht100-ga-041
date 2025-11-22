#!/bin/bash

# ============================================================================
# The Empathy Engine - Demo Script
# Tests the /analyze endpoint with sample conversation
# ============================================================================

echo "╔════════════════════════════════════════╗"
echo "║   THE EMPATHY ENGINE - API Demo       ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Configuration
API_URL="http://localhost:8000"
DEMO_FILE="demo/conversation.json"

# Check if backend is running
echo "[1/3] Checking if backend is running..."
if ! curl -s "$API_URL/" > /dev/null; then
    echo "❌ Backend not running. Start it with:"
    echo "   cd backend && python main.py"
    exit 1
fi
echo "✓ Backend is online"
echo ""

# Test /analyze endpoint
echo "[2/3] Testing POST /analyze endpoint..."
echo ""

RESPONSE=$(curl -s -X POST "$API_URL/analyze" \
  -H "Content-Type: application/json" \
  -d @"$DEMO_FILE")

echo "$RESPONSE" | python -m json.tool

echo ""
echo "✓ Analysis complete"
echo ""

# Test /summary endpoint
echo "[3/3] Testing POST /summary endpoint..."
echo ""

SUMMARY=$(curl -s -X POST "$API_URL/summary" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo1"}')

echo "$SUMMARY" | python -m json.tool

echo ""
echo "╔════════════════════════════════════════╗"
echo "║   Demo Complete!                       ║"
echo "║   Check the emotion timeline above     ║"
echo "╚════════════════════════════════════════╝"
