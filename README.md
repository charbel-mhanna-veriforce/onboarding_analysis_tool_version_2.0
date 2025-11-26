# Onboarding Analysis Tool v2.0

## 📋 Overview

The **Onboarding Analysis Tool** is a powerful web application designed to match contractor records between Cognibox (CBX) database and Hiring Client (HC) submissions using advanced fuzzy matching algorithms. Built with React + FastAPI, it provides real-time progress tracking and generates comprehensive Excel reports.

## ✨ Key Features

### 🔍 **Intelligent Matching**
- **Fuzzy string matching** for company names (English/French support)
- **Address validation** with postal code comparison
- **Email domain matching** (corporate vs. personal email detection)
- **Historical name tracking** (matches against previous company names)
- **Contact verification** across multiple fields
- **Generic domain filtering** (yahoo, gmail, hotmail, etc.)

### ⚡ **Real-Time Monitoring**
- **Live progress bar** with percentage completion (0-100%)
- **Timer display** showing elapsed processing time
- **Record counter** (processed/total)
- **Live console logs** with color-coded messages
- **Background processing** with async job tracking

### 📊 **Comprehensive Reports**
- **Excel output** with 12+ categorized sheets
- **Action-based filtering** (onboarding, re-onboarding, etc.)
- **Match analysis** with ratio scores
- **Subscription upgrade calculations**
- **Metadata preservation** from source files

### 🎨 **Modern UI/UX**
- Beautiful gradient design with purple/blue theme
- Responsive layout for all screen sizes
- Animated transitions and smooth interactions
- Terminal-style live console
- Dashboard with statistics

## 🏗️ Architecture

```
Frontend (React + Vite)          Backend (FastAPI + Python)
┌─────────────────────┐         ┌─────────────────────────┐
│  Upload Interface   │────────▶│  File Upload Handler    │
│  Progress Tracker   │◀────────│  Background Jobs        │
│  Live Console       │◀────────│  Matching Engine        │
│  Download Manager   │◀────────│  Excel Generator        │
└─────────────────────┘         └─────────────────────────┘
         │                                   │
         │                                   │
    Port 5173                           Port 8000
```

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Modern web browser** (Chrome, Firefox, Edge)

### Installation

**1. Clone the repository**
```bash
git clone <repository-url>
cd onboarding_analysis_tool_version_2.0
```

**2. Install backend dependencies**
```bash
cd backend
pip install -r requirements.txt
```

**3. Install frontend dependencies**
```bash
cd ../frontend
npm install
```

### Running the Application

#### Option 1: Quick Start (Two Terminals)

**Terminal 1 - Backend:**
```bash
cd backend
python3 main.py
```
✅ Backend starts at `http://localhost:8000`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```
✅ Frontend starts at `http://localhost:5173`

**Open browser:** Navigate to `http://localhost:5173`

#### Option 2: Using Scripts (Linux/WSL)

**Start backend:**
```bash
cd backend
./start.sh
```

**Restart backend:**
```bash
cd backend
./restart.sh
```

## 📖 How to Use

### Step 1: Prepare Your Files

**CBX File (Cognibox Database Export)**
- Format: CSV, XLSX, or XLS
- Required columns (28 total):
  - `id`, `name_fr`, `name_en`, `old_names`
  - `address`, `city`, `state`, `country`, `postal_code`
  - `first_name`, `last_name`, `email`
  - `cbx_expiration_date`, `registration_code`, `suspended`
  - `modules`, `access_modes`, `code`
  - `subscription_price_cad`, `employee_price_cad`
  - `subscription_price_usd`, `employee_price_usd`
  - `hiring_client_names`, `hiring_client_ids`, `hiring_client_qstatus`
  - `parents`, `assessment_level`, `new_product`

**HC File (Hiring Client Submissions)**
- Format: CSV, XLSX, or XLS
- Required columns (41 total):
  - `contractor_name`, `contact_first_name`, `contact_last_name`, `contact_email`
  - `contact_phone`, `contact_language`
  - `address`, `city`, `province_state_iso2`, `country_iso2`, `postal_code`
  - `category`, `description`, `phone`, `extension`, `fax`, `website`, `language`
  - `is_take_over`, `qualification_expiration_date`, `qualification_status`
  - `batch`, `questionnaire_name`, `questionnaire_id`
  - `pricing_group_id`, `pricing_group_code`
  - `hiring_client_name`, `hiring_client_id`
  - `is_association_fee`, `base_subscription_fee`
  - `contact_currency`, `agent_in_charge_id`
  - `take_over_follow-up_date`, `renewal_date`
  - `information_shared`, `contact_timezone`
  - `do_not_match`, `force_cbx_id`, `ambiguous`
  - `contractorcheck_account`, `assessment_level`

### Step 2: Upload and Process

1. **Open the application** at `http://localhost:5173`
2. **Click "Upload" tab**
3. **Select CBX file** (drag & drop or click to browse)
4. **Select HC file** (drag & drop or click to browse)
5. **Click "Start Matching"** button
6. **Monitor progress:**
   - Progress bar shows completion percentage
   - Timer shows elapsed time
   - Counter shows records processed
   - Console displays detailed logs

### Step 3: Download Results

1. Wait for **"Processing Complete!"** status
2. Click **"Download Results"** button
3. Open the Excel file in your preferred application

### Step 4: Analyze Results

**Output Excel File Contains:**

1. **all** - Complete dataset with all matches and analysis
2. **onboarding** - New contractors requiring onboarding
3. **re_onboarding** - Inactive contractors to reactivate
4. **add_questionnaire** - Active contractors needing questionnaires
5. **already_qualified** - Contractors already validated
6. **follow_up_qualification** - Contractors requiring follow-up
7. **activation_link** - Contractors needing activation
8. **ambiguous_onboarding** - Ambiguous matches requiring review
9. **association_fee** - Contractors requiring association fees
10. **subscription_upgrade** - Contractors requiring plan upgrades
11. **restore_suspended** - Suspended accounts to restore
12. **missing_info** - Incomplete submissions

**Key Columns in Output:**
- `cbx_id` - Matched Cognibox ID (blank if new)
- `analysis` - Detailed match information with scores
- `ratio_company` - Company name match score (0-100)
- `ratio_address` - Address match score (0-100)
- `contact_match` - Email/contact match (TRUE/FALSE)
- `action` - Recommended action
- `create_in_cbx` - Whether to create new record
- `is_subscription_upgrade` - Upgrade required
- `match_count` - Number of potential matches found

## 🔧 Configuration

### Matching Algorithm

The tool uses **legacy-tested matching logic** with the following rules:

**Company Name Matching:**
- Compares against both French and English names
- Checks historical/previous names
- Removes generic words (inc, ltd, construction, etc.)
- Uses fuzzy token sort ratio
- **Default threshold: 80%**

**Address Matching:**
- Combines street address and postal code
- Only compares within same country
- Uses weighted combination of address and zip ratio
- **Default threshold: 80%**

**Email Matching:**
- For generic domains (gmail, yahoo, etc.): exact email match required
- For corporate domains: domain-level match accepted
- Helps avoid false positives

**Priority Rules:**
1. Forced matches (if `force_cbx_id` provided)
2. Contact matches (email/domain)
3. High company name ratio (≥95%) regardless of address
4. Combined company + address threshold match
5. Matches with hiring client relationship
6. Active registration status preferred
7. Higher module count preferred

### Custom Configuration

The matching thresholds are **hardcoded to legacy defaults (80/80)** for consistency with historical processing. These values have been tested and validated across thousands of contractor records.

## 🛠️ Development

### Backend Structure

```python
backend/
├── main.py                 # Main FastAPI application
├── convertTimeZone.py      # Timezone conversion utilities
├── requirements.txt        # Python dependencies
├── uploads/               # Temporary file storage
└── outputs/               # Generated Excel files
```

**Key Dependencies:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `openpyxl` - Excel file handling
- `fuzzywuzzy` - Fuzzy string matching
- `python-Levenshtein` - Fast string comparison

### Frontend Structure

```javascript
frontend/
├── src/
│   ├── App.jsx            # Main React component
│   ├── main.jsx          # React entry point
│   └── index.css         # Tailwind + custom styles
├── index.html            # HTML template
├── package.json          # Dependencies
├── vite.config.js        # Vite configuration
└── tailwind.config.js    # Tailwind configuration
```

**Key Dependencies:**
- `react` - UI framework
- `lucide-react` - Icon library
- `tailwindcss` - CSS framework
- `vite` - Build tool

### API Endpoints

**POST /api/match**
- Uploads files and starts matching job
- Returns: `job_id`, `status`, `progress`, `message`

**GET /api/jobs/{job_id}**
- Retrieves job status
- Returns: Current progress, status, message, errors

**GET /api/jobs/{job_id}/download**
- Downloads completed Excel results
- Returns: Excel file as attachment

**GET /api/jobs**
- Lists all jobs
- Returns: Array of job statuses

**GET /api/health**
- Health check endpoint
- Returns: System status

## 🐛 Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`
```bash
cd backend
pip install -r requirements.txt
```

**Problem:** Port 8000 already in use
```bash
# Find and kill process on port 8000
lsof -i :8000
kill -9 <PID>
```

**Problem:** Permission denied on start.sh
```bash
chmod +x start.sh restart.sh
```

### Frontend Issues

**Problem:** `ECONNREFUSED` backend connection error
- Ensure backend is running on port 8000
- Check CORS is enabled in backend

**Problem:** Files not uploading
- Check file size limits (backend default: unlimited)
- Verify file format (CSV, XLSX, XLS)
- Check browser console for errors

**Problem:** Progress stuck at 0%
- Check backend logs for processing errors
- Verify file headers match expected format
- Check backend console output

### Common Data Issues

**Problem:** No matches found
- Verify file formats match expected headers
- Check for encoding issues (use UTF-8)
- Review company name cleaning logic

**Problem:** Too many matches
- Increase matching thresholds (requires code change)
- Add more generic company words to filter

**Problem:** Incorrect actions assigned
- Review business logic in `action()` function
- Check registration status values
- Verify subscription pricing data

## 📝 Testing

### Manual Testing

**1. Test with sample data:**
```bash
cd backend/testdata
# Use cbx.csv and hc.csv for testing
```

**2. Run diagnostic test:**
```bash
cd backend
python test_diagnostic.py
```

**3. Check background processing:**
```bash
cd backend
python test_background.py
```

### Integration Testing

```bash
cd backend
python test_integration.py
```

## 📊 Performance

**Typical Processing Times:**
- 100 contractors: ~30-60 seconds
- 500 contractors: ~2-5 minutes
- 1000 contractors: ~5-10 minutes
- 5000 contractors: ~25-50 minutes

**Factors Affecting Speed:**
- Number of CBX records (larger database = slower)
- Number of HC records to process
- File format (CSV faster than Excel)
- System resources (CPU, RAM)

## 🔐 Security Considerations

- Files are stored temporarily in `uploads/` folder
- Results stored in `outputs/` folder
- No authentication implemented (internal use only)
- Sensitive data should not be committed to git
- Use `.gitignore` to exclude data files

## 📄 License

Internal use only. All rights reserved.

## 👥 Support

For issues, questions, or feature requests:
1. Check TROUBLESHOOTING.md
2. Review backend logs in `backend.log`
3. Check browser console for frontend errors
4. Contact development team

## 🗺️ Roadmap

Potential future enhancements:
- [ ] User authentication and multi-tenancy
- [ ] Database storage for job history
- [ ] Configurable matching thresholds via UI
- [ ] Batch processing queue
- [ ] Email notifications on completion
- [ ] API rate limiting
- [ ] Docker containerization
- [ ] Export to multiple formats (CSV, JSON)
- [ ] Advanced filtering and search in results
- [ ] Audit trail and logging

---

**Version:** 2.0  
**Last Updated:** November 2025  
**Status:** Production Ready ✅

