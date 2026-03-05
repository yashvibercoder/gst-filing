#!/bin/bash
# GST Filing - Start Portal (Linux/Mac)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo " GST Filing - Starting Portal"
echo "============================================"
echo ""

# Build frontend if dist doesn't exist
if [ ! -d "portal/frontend/dist" ]; then
    echo "Building frontend (first run)..."
    cd portal/frontend
    npm run build
    cd "$SCRIPT_DIR"
fi

echo "Starting backend on http://localhost:8000 ..."
echo "Press Ctrl+C to stop."
echo ""

source portal/backend/venv/bin/activate
python -m uvicorn portal.backend.app.main:app --port 8000
