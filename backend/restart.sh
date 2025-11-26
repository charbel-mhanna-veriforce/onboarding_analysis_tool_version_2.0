#!/bin/bash

echo "=========================================="
echo "  Onboarding Analysis Tool - Restart"
echo "=========================================="
echo ""

# Navigate to backend
cd "$(dirname "$0")"

# Stop existing backend
echo "Stopping existing backend..."
pkill -f "python.*main.py" 2>/dev/null || true
sleep 2

# Backup old main.py if main_v2.py exists
if [ -f "main_v2.py" ]; then
    echo "Backing up old main.py..."
    cp main.py main_old_backup.py 2>/dev/null || true
    cp main_v2.py main.py
    echo "✓ New version installed"
fi

# Clean up old files
echo "Cleaning up old job files..."
find uploads/ -type f -mtime +1 -delete 2>/dev/null || true
find outputs/ -type f -mtime +1 -delete 2>/dev/null || true

# Start backend
echo ""
echo "Starting backend server..."
echo "Logs will be written to backend.log"
echo ""

python3 main.py > backend.log 2>&1 &
BACKEND_PID=$!

sleep 3

# Check if backend started
if ps -p $BACKEND_PID > /dev/null; then
    echo "✓ Backend started successfully (PID: $BACKEND_PID)"
    echo "✓ API running at: http://localhost:8000"
    echo ""
    echo "View logs with: tail -f backend/backend.log"
    echo "Stop with: pkill -f 'python.*main.py'"
    echo ""
    echo "=========================================="
else
    echo "✗ Backend failed to start!"
    echo "Check backend.log for errors"
    exit 1
fi

