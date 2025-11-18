# User Guide

## 📖 Table of Contents
1. [Getting Started](#getting-started)
2. [Preparing Your Data](#preparing-your-data)
3. [Uploading Files](#uploading-files)
4. [Configuring Match Settings](#configuring-match-settings)
5. [Processing Data](#processing-data)
6. [Understanding Results](#understanding-results)
7. [Using the Dashboard](#using-the-dashboard)
8. [Best Practices](#best-practices)
9. [FAQ](#faq)

---

## 🚀 Getting Started

### Opening the Application

1. **Start the Backend**
   ```bash
   cd backend
   python3 main.py
   ```
   Wait for: `Uvicorn running on http://0.0.0.0:8000`

2. **Start the Frontend**
   ```bash
   cd frontend
   npm run dev
   ```
   Wait for: `Local: http://localhost:5173/`

3. **Open in Browser**
   Navigate to: `http://localhost:5173`

### First Look

You'll see the dashboard with:
- **Statistics Cards** at the top
- **Tab Navigation** (Upload, History, Logs)
- **Live Console** at the bottom

---

## 📊 Preparing Your Data

### CBX File (Contractors Database)

**Required Format**: CSV or Excel (.csv, .xlsx, .xls)

**Required Columns**:
- `id` - Unique contractor ID
- `name_en` - Company name (English)
- `name_fr` - Company name (French) - optional
- `email` - Contact email
- `address` - Physical address
- `postal_code` - Postal/ZIP code
- `country` - Country code (CA, US, etc.)
- `registration_code` - Status (Active, Suspended, etc.)
- `modules` - Assessment levels
- `hiring_client_names` - Semicolon-separated list
- `old_names` - Previous company names (optional)

**Example CBX Data**:
```csv
id,name_en,email,address,postal_code,country,registration_code
12345,ABC Construction Inc,info@abc.com,123 Main St,M5V 2T6,CA,Active
67890,XYZ Services Ltd,contact@xyz.com,456 Oak Ave,90210,US,Suspended
```

### HC File (Hiring Client Submissions)

**Required Format**: CSV or Excel (.csv, .xlsx, .xls)

**Required Columns**:
- `contractor_name` - Company name to match
- `contact_email` - Contact email
- `address` - Physical address
- `postal_code` - Postal/ZIP code
- `country_iso2` - Country code (CA, US, etc.)
- `hiring_client_name` - Name of hiring client
- `is_take_over` - Boolean (TRUE/FALSE) for takeover scenarios
- `ambiguous` - Boolean (TRUE/FALSE) if data is ambiguous

**Example HC Data**:
```csv
contractor_name,contact_email,address,postal_code,country_iso2,hiring_client_name,is_take_over
ABC Construction,info@abc.com,123 Main Street,M5V2T6,CA,BigCorp Inc,FALSE
XYZ Services,contact@xyz.com,456 Oak Avenue,90210,US,MegaCorp LLC,TRUE
```

### Data Quality Tips

✅ **DO**:
- Use consistent formatting
- Include all required columns
- Remove duplicate header rows
- Verify email addresses are valid
- Ensure postal codes are clean (no extra spaces)

❌ **DON'T**:
- Use merged cells
- Include summary rows
- Mix languages in one field
- Leave required fields empty
- Use special characters in column names

---

## 📤 Uploading Files

### Step-by-Step Upload Process

1. **Navigate to Upload Tab**
   - Click on **"Upload"** tab at the top
   - You'll see the upload form

2. **Select CBX File**
   - Click **"CBX Database File"** area
   - Browse and select your contractors database file
   - Supported formats: .csv, .xlsx, .xls
   - You'll see: ✅ "File selected: filename.xlsx"

3. **Select HC File**
   - Click **"Hiring Client File"** area
   - Browse and select your HC submissions file
   - Supported formats: .csv, .xlsx, .xls
   - You'll see: ✅ "File selected: filename.csv"

4. **Verify Files**
   - Check the file names are correct
   - Both files must be selected to proceed
   - To change a file, click the area again

### File Size Limits

- **Maximum size**: No hard limit (recommended < 100MB)
- **Processing time**: ~1-5 minutes for 1,000 records
- **Large files**: Consider splitting into smaller batches

---

## ⚙️ Configuring Match Settings

### Matching Thresholds

Before processing, you can adjust matching sensitivity:

#### Company Name Match Threshold (Default: 80%)

**What it does**: Determines how similar company names must be to match.

- **90-100%**: Very strict - Only near-exact matches
  - Good for: Clean data with consistent naming
  - Example: "ABC Inc" matches "ABC Inc." but not "ABC Incorporated"

- **80-89%**: Balanced - Recommended for most cases
  - Good for: Real-world data with minor variations
  - Example: "ABC Construction Inc" matches "ABC Construction"

- **60-79%**: Relaxed - More matches, more false positives
  - Good for: Data with many variations
  - Example: "ABC" matches "ABC Services"

- **< 60%**: Very relaxed - Use with caution
  - Risk of incorrect matches
  - Requires manual review

#### Address Match Threshold (Default: 80%)

**What it does**: Determines how similar addresses must be to match.

- **90-100%**: Very strict
  - Example: "123 Main Street" matches "123 Main St." only

- **80-89%**: Balanced - Recommended
  - Example: "123 Main Street" matches "123 Main St"

- **60-79%**: Relaxed
  - Example: "123 Main" matches "123 Main Street"

### Adjusting Thresholds

1. Use the **sliders** in the upload form
2. Watch the **percentage value** update in real-time
3. Hover over slider to see tooltip (if implemented)

**Pro Tip**: Start with default values (80%), review results, then adjust if needed.

---

## 🎯 Processing Data

### Starting the Process

1. **Click "Start Matching" Button**
   - Button turns gray and shows spinner icon
   - Text changes to "Processing..."
   - Button becomes disabled

2. **Watch Real-Time Progress**

   **Progress Bar**: Shows completion percentage
   - Animated gradient bar (blue → indigo → purple)
   - Percentage displayed: "45%"
   - Smooth transitions as progress updates

   **Timer**: Shows elapsed time
   - Format: `MM:SS` (e.g., "02:35")
   - Or: `HH:MM:SS` for long jobs (e.g., "1:05:23")
   - Updates every second

   **Record Counter**: Shows records processed
   - Format: "45 / 100"
   - Updates in real-time

   **Status Message**: Shows current activity
   - "Uploading files..."
   - "Reading CBX data..."
   - "Building indexes..."
   - "Matching contractors... (45/100)"
   - "Generating output file..."

3. **Monitor Live Console**

   Scroll to the bottom of the page to see the **Live Console**:
   ```
   14:32:15 [INFO]    Starting new matching job...
   14:32:16 [INFO]    File selected: cbx_data.xlsx
   14:32:17 [INFO]    File selected: hc_data.csv
   14:32:18 [SUCCESS] Job created: abc-123-def-456
   14:32:19 [INFO]    Poll: processing - 5% - Matching...
   14:32:20 [INFO]    Progress: 5/100 records
   ```

### Processing Stages

1. **Uploading** (1-5 seconds)
   - Files sent to backend
   - Job ID created

2. **Reading Data** (5-30 seconds)
   - Files parsed
   - Data loaded into memory
   - Columns validated

3. **Building Indexes** (2-10 seconds)
   - Email domains indexed
   - Company names indexed
   - Faster matching preparation

4. **Matching** (Main stage - 60-90% of time)
   - Each HC record matched against CBX
   - Progress updates every record
   - Real-time percentage shown

5. **Generating Output** (5-15 seconds)
   - Results compiled
   - Excel file created
   - Multiple sheets organized

6. **Complete** (Instant)
   - Green checkmark appears
   - Download button enabled
   - Final stats displayed

### Expected Processing Times

| Records | Time |
|---------|------|
| 10 | 5-10 seconds |
| 100 | 30-60 seconds |
| 500 | 2-4 minutes |
| 1,000 | 4-8 minutes |
| 5,000 | 20-40 minutes |

*Times vary based on system performance and data complexity*

### If Processing Seems Stuck

1. **Check the Live Console** - Is it updating?
2. **Check Backend Terminal** - Are there error messages?
3. **Wait patiently** - Large datasets take time
4. **Check browser console** (F12) - Any JavaScript errors?

---

## 📥 Understanding Results

### Downloading Results

1. **Wait for Completion**
   - Status: "Processing Complete!"
   - Green checkmark icon appears
   - Timer stops

2. **Click "Download Results"**
   - Excel file downloads automatically
   - File name: `{job-id}_results.xlsx`
   - File saved to your Downloads folder

### Result File Structure

The Excel file contains **multiple sheets**:

#### Sheet 1: "All Results"
Complete dataset with all matches and recommendations.

**Columns**:
- All original HC columns
- `matched_cbx_id` - ID of matched contractor (if found)
- `matched_company` - Name of matched company
- `matched_email` - Email of matched contractor
- `match_ratio_company` - Name match score (0-100)
- `match_ratio_address` - Address match score (0-100)
- `match_contact` - Email/contact matched (TRUE/FALSE)
- `match_status` - CBX status (Active/Suspended/etc.)
- `match_count` - Number of potential matches found
- `action` - **Recommended action** (see below)

#### Sheet 2-N: Action-Specific Sheets

Each recommended action gets its own sheet for easy filtering:

1. **"onboarding"** - New contractors to onboard
2. **"add_questionnaire"** - Send questionnaire to existing contractors
3. **"already_qualified"** - Already working with this client
4. **"re_onboarding"** - Reactivate inactive contractors
5. **"restore_suspended"** - Restore suspended accounts
6. **"activation_link"** - Send activation link
7. **"ambiguous_onboarding"** - Unclear cases needing review

### Action Definitions

| Action | Meaning | What To Do |
|--------|---------|------------|
| **onboarding** | No match found in CBX | Create new contractor profile |
| **add_questionnaire** | Matched, need assessment | Send safety questionnaire |
| **already_qualified** | Already qualified for this client | No action needed ✅ |
| **re_onboarding** | Found but inactive | Reactivate and update profile |
| **restore_suspended** | Account suspended | Restore account access |
| **activation_link** | Registered but not activated | Resend activation email |
| **ambiguous_onboarding** | Data unclear | Manual review required |

### Interpreting Match Scores

#### Company Name Match (match_ratio_company)

- **95-100**: Excellent match - Very confident
  - "ABC Construction Inc" vs "ABC Construction Inc."

- **85-94**: Good match - Confident
  - "ABC Construction Inc" vs "ABC Construction"

- **80-84**: Fair match - Review recommended
  - "ABC Construction" vs "ABC Contracting"

- **< 80**: Poor match - Likely different companies
  - "ABC" vs "XYZ"

#### Address Match (match_ratio_address)

- **95-100**: Same address
- **85-94**: Very similar (abbreviations, formatting)
- **80-84**: Similar street/area
- **< 80**: Different addresses

### Manual Review Recommendations

**Always review manually if**:
- Match score is 80-85 (borderline)
- Action is "ambiguous_onboarding"
- Multiple potential matches (match_count > 1)
- Critical data (high-value contractors)

---

## 📊 Using the Dashboard

### Statistics Overview (Top Cards)

**Total Jobs**
- Shows total number of jobs processed
- Includes successful and failed jobs
- Updated after each job completes

**Success Rate**
- Percentage of successful vs failed jobs
- Green = good, Red = needs attention
- Target: > 95%

**Records Processed**
- Total contractor records processed across all jobs
- Lifetime counter

**Average Time**
- Average processing time per job
- Helps estimate future job durations
- Format: MM:SS or HH:MM:SS

### Tabs

#### 1. Upload Tab

The main interface for processing data:
- File upload areas
- Matching threshold sliders
- Start processing button
- Real-time progress display (when processing)
- Download button (when complete)

#### 2. History Tab

View all past jobs:

**Features**:
- **Search bar**: Find jobs by ID, file name, status
- **Filter dropdown**: Show all, completed, failed, processing
- **Sort options**: By date, status, records count

**Job Cards Show**:
- Job ID (unique identifier)
- Status badge (Completed/Failed/Processing)
- Created date and time
- Total records processed
- Processing duration
- Action buttons:
  - 📥 **Download**: Get results file (if completed)
  - 🔄 **Reload**: Retry failed job
  - 🗑️ **Delete**: Remove from history

**Actions**:
- Click **Download** to re-download results
- Click job card to see details
- Use search to find specific jobs
- Filter by status to focus on issues

#### 3. Logs Tab

View detailed logs in card format:

**Features**:
- Color-coded log cards (info, success, warning, error)
- Timestamps for each log
- Icons for log types
- Scroll to view history

**Log Types**:
- 🔵 **Info** (Blue): General information
- 🟢 **Success** (Green): Successful operations
- 🟡 **Warning** (Yellow): Non-critical issues
- 🔴 **Error** (Red): Errors requiring attention

### Live Console (Bottom of Page)

**Features**:
- Terminal-style dark interface
- Real-time log streaming
- Auto-scrolls to latest logs
- Color-coded messages
- Timestamps in HH:MM:SS format

**Controls**:
- **Clear button**: Reset console
- **Log counter**: Shows total logs

**Reading Logs**:
```
14:32:15 [INFO]    Message here
 ^         ^        ^
 |         |        └─ Log message
 |         └─ Log type
 └─ Timestamp
```

---

## 💡 Best Practices

### Data Preparation

1. **Clean your data first**
   - Remove blank rows
   - Standardize formatting
   - Verify email addresses

2. **Use consistent naming**
   - Same company name format across files
   - Consistent address abbreviations

3. **Test with small dataset**
   - Process 10-20 records first
   - Review results
   - Adjust thresholds if needed

### Threshold Selection

1. **Start with defaults** (80%)
2. **Review first batch of results**
3. **Adjust if needed**:
   - Too many misses → Lower threshold
   - Too many false matches → Raise threshold

### Processing Large Datasets

1. **Split into batches** (< 1,000 records each)
2. **Process during off-hours** (if possible)
3. **Monitor console** for errors
4. **Save results immediately** after completion

### Review Process

1. **Download results immediately**
2. **Review "All Results" sheet first**
3. **Check match scores** (< 85 needs review)
4. **Validate action sheets**
5. **Look for patterns** in mismatches

### Error Handling

1. **Check Live Console** first
2. **Review backend terminal** logs
3. **Verify file formats** are correct
4. **Check data quality** (missing columns, bad data)
5. **Try smaller dataset** to isolate issue

---

## ❓ FAQ

### General Questions

**Q: What file formats are supported?**
A: CSV (.csv), Excel (.xlsx, .xls) for both input and output.

**Q: Can I process multiple jobs simultaneously?**
A: Yes, the backend supports multiple concurrent jobs.

**Q: How long are results stored?**
A: Results are stored in `backend/outputs/` until manually deleted.

**Q: Can I re-download old results?**
A: Yes, use the History tab to find and download past results.

### Matching Questions

**Q: Why didn't my contractor match?**
A: Possible reasons:
- Name spelling differences exceed threshold
- Different email domain
- Address mismatch
- Company not in CBX database

**Q: What if there are multiple matches?**
A: The algorithm picks the best match based on:
1. Hiring client relationship
2. Active status
3. Match scores
4. Email/contact match

**Q: Can I see all potential matches?**
A: The `match_count` column shows how many matches were found. Only the best match is shown in results.

**Q: How are French company names handled?**
A: Both `name_en` and `name_fr` are checked. The highest score wins.

### Technical Questions

**Q: Why is processing slow?**
A: Factors affecting speed:
- Dataset size (larger = slower)
- System resources (CPU, RAM)
- Data complexity (more variations = slower)
- CBX database size

**Q: Can I cancel a running job?**
A: Currently, no. Let it complete or restart the backend server.

**Q: Where are uploaded files stored?**
A: Temporarily in `backend/uploads/`. They can be deleted after processing.

**Q: Is my data secure?**
A: Files are stored locally. No data is sent to external servers.

### Troubleshooting Questions

**Q: Progress bar stuck at 0%?**
A: Check:
1. Live Console - Is it updating?
2. Backend terminal - Any errors?
3. Browser console (F12) - JavaScript errors?

**Q: Download button not working?**
A: 
1. Wait for "Processing Complete!" message
2. Check backend terminal for errors
3. Verify file exists in `backend/outputs/`

**Q: "Job not found" error?**
A: The job may have been deleted or backend restarted. Try uploading again.

**Q: Getting "CORS error"?**
A: Check:
1. Backend is running on port 8000
2. Frontend URL is `http://localhost:5173`
3. CORS is configured correctly in `main.py`

---

## 📞 Need More Help?

1. **Check the logs** - Live Console and backend terminal
2. **Review documentation** - README.md, API docs
3. **Test with sample data** - Use provided example files
4. **Contact support** - Reach out to development team

---

**Happy Matching!** 🎉

For technical details, see `API_DOCUMENTATION.md` and `TECHNICAL_GUIDE.md`.

