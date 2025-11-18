# Installation Guide

## 📦 System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Linux (Ubuntu 20.04+)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 500MB for application + space for data files
- **Internet**: Required for initial setup and package downloads

### Software Prerequisites
- **Python 3.8 or higher** - Backend runtime
- **Node.js 16 or higher** - Frontend build tools
- **npm 8 or higher** - Node package manager
- **pip 21 or higher** - Python package manager

## 🔍 Checking Prerequisites

### Check Python Version
```bash
python3 --version
# Should output: Python 3.8.x or higher
```

### Check Node.js Version
```bash
node --version
# Should output: v16.x.x or higher
```

### Check npm Version
```bash
npm --version
# Should output: 8.x.x or higher
```

### Check pip Version
```bash
pip3 --version
# Should output: pip 21.x.x or higher
```

## 📥 Installing Prerequisites

### Installing Python

**Windows:**
1. Download from https://www.python.org/downloads/
2. Run installer
3. ✅ Check "Add Python to PATH"
4. Click "Install Now"

**macOS:**
```bash
# Using Homebrew
brew install python@3.11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3-pip
```

### Installing Node.js

**Windows & macOS:**
1. Download from https://nodejs.org/
2. Download the LTS version
3. Run installer and follow prompts

**Linux (Ubuntu/Debian):**
```bash
# Using NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

## 🚀 Installation Steps

### Step 1: Download the Project

**Option A: Using Git**
```bash
git clone <repository-url>
cd onboarding_analysis_tool_version_2.0
```

**Option B: Manual Download**
1. Download the project ZIP file
2. Extract to your desired location
3. Open terminal/command prompt in the project folder

### Step 2: Backend Setup

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment** (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

Expected output:
```
Collecting fastapi
Collecting uvicorn
Collecting pandas
Collecting rapidfuzz
...
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 pandas-2.1.3 ...
```

4. **Verify installation**
```bash
python3 -c "import fastapi, pandas, rapidfuzz; print('✓ All backend dependencies installed')"
```

### Step 3: Frontend Setup

1. **Navigate to frontend directory** (from project root)
```bash
cd frontend
```

2. **Install Node.js dependencies**
```bash
npm install
```

Expected output:
```
added 234 packages in 45s
```

3. **Verify installation**
```bash
npm list --depth=0
```

Should show packages like:
- react
- vite
- tailwindcss
- lucide-react

### Step 4: Verify Installation

**Test Backend**
```bash
cd backend
python3 main.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Press `Ctrl+C` to stop.

**Test Frontend**
```bash
cd frontend
npm run dev
```

Expected output:
```
VITE v5.0.0  ready in 1234 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

Press `Ctrl+C` to stop.

## 🎯 Post-Installation Setup

### Create Required Directories

The application will create these automatically, but you can create them manually:

```bash
cd backend
mkdir -p uploads outputs
```

### Set File Permissions (Linux/macOS)

```bash
chmod 755 backend/uploads
chmod 755 backend/outputs
```

### Configure Environment Variables (Optional)

Create `.env` file in backend directory:
```bash
cd backend
nano .env
```

Add configuration:
```env
# Backend Configuration
HOST=0.0.0.0
PORT=8000

# File Upload
MAX_UPLOAD_SIZE=100MB
UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs

# Logging
LOG_LEVEL=INFO
```

## 🔧 Troubleshooting Installation

### Issue: Python not found

**Windows:**
```bash
# Add Python to PATH manually
# Go to: System Properties > Environment Variables
# Add: C:\Python311 and C:\Python311\Scripts to PATH
```

**macOS/Linux:**
```bash
# Create symlink
sudo ln -s /usr/bin/python3 /usr/bin/python
```

### Issue: pip install fails with permission error

**Solution:**
```bash
# Use --user flag
pip install --user -r requirements.txt

# Or use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Issue: npm install fails

**Solution 1: Clear cache**
```bash
npm cache clean --force
npm install
```

**Solution 2: Delete node_modules**
```bash
rm -rf node_modules package-lock.json
npm install
```

**Solution 3: Use different registry**
```bash
npm install --registry https://registry.npmjs.org/
```

### Issue: Port already in use

**Backend (Port 8000):**
```bash
# Linux/macOS
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Frontend (Port 5173):**
Vite will automatically use the next available port (5174, 5175, etc.)

### Issue: Module not found errors

**Backend:**
```bash
# Reinstall specific package
pip install fastapi --upgrade

# Or reinstall all
pip install -r requirements.txt --force-reinstall
```

**Frontend:**
```bash
# Reinstall specific package
npm install react@latest

# Or reinstall all
rm -rf node_modules
npm install
```

### Issue: Python virtual environment not activating

**Windows PowerShell:**
```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Windows CMD:**
```cmd
# Use activate.bat instead
venv\Scripts\activate.bat
```

## ✅ Installation Verification Checklist

Run these commands to verify everything is installed:

```bash
# 1. Check Python
python3 --version

# 2. Check Node
node --version

# 3. Check npm
npm --version

# 4. Test backend imports
python3 -c "import fastapi, pandas, rapidfuzz; print('✓ Backend OK')"

# 5. Test frontend build
cd frontend && npm run build && echo "✓ Frontend OK"

# 6. Check directory structure
ls -la backend/uploads backend/outputs
```

All checks should pass ✅

## 🎉 Next Steps

After successful installation:

1. **Read the User Guide**: `docs/USER_GUIDE.md`
2. **Review API Documentation**: `docs/API_DOCUMENTATION.md`
3. **Check Configuration**: `docs/CONFIGURATION.md`
4. **Start the application**: Follow Quick Start in README.md

## 📞 Getting Help

If you encounter issues not covered here:

1. Check the **Troubleshooting** section above
2. Review backend/frontend logs for errors
3. Ensure all prerequisites are installed correctly
4. Check system requirements are met
5. Contact the development team

## 🔄 Updating the Application

To update to a newer version:

```bash
# Pull latest changes (if using git)
git pull origin main

# Update backend dependencies
cd backend
pip install -r requirements.txt --upgrade

# Update frontend dependencies
cd frontend
npm update

# Rebuild frontend
npm run build
```

---

**Installation Complete!** 🎉

You're now ready to use the Onboarding Analysis Tool v2.0.

Start the application by following the **Quick Start** section in the main README.md file.

