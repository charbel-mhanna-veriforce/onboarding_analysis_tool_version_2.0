#!/bin/bash
# Quick setup and start script for the backend

echo "=================================="
echo "Backend Quick Start"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "Error: main.py not found!"
    echo "Please run this script from the backend directory"
    exit 1
fi

# Create required directories
echo ""
echo "1. Creating directories..."
mkdir -p uploads outputs
echo "   ✓ uploads/ and outputs/ ready"

# Install/update dependencies
echo ""
echo "2. Installing dependencies..."
pip install -q requests 2>/dev/null || pip3 install -q requests 2>/dev/null
echo "   ✓ requests installed"

# Check if all dependencies are installed
echo ""
echo "3. Checking Python modules..."
python3 -c "
import sys
missing = []
for module in ['fastapi', 'uvicorn', 'pandas', 'rapidfuzz', 'openpyxl']:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)

if missing:
    print(f'   Missing modules: {missing}')
    print('   Installing from requirements.txt...')
    sys.exit(1)
else:
    print('   ✓ All core modules present')
    sys.exit(0)
"

if [ $? -ne 0 ]; then
    echo "   Installing missing modules..."
    pip install -r requirements.txt || pip3 install -r requirements.txt
fi

# Kill any existing process on port 8000
echo ""
echo "4. Checking port 8000..."
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "   Killing existing process on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi
echo "   ✓ Port 8000 is available"

# Start the backend
echo ""
echo "5. Starting backend server..."
echo "=================================="
echo ""
echo "Backend will start on http://localhost:8000"
echo "Watch for these key logs:"
echo "  - 'Uvicorn running on http://0.0.0.0:8000'"
echo "  - '!!!! BACKGROUND TASK STARTED' (when you upload files)"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "=================================="
echo ""

python3 main.py

