# Technical Guide

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (Client)                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  React Frontend (Vite)                               │   │
│  │  - UI Components (App.jsx)                           │   │
│  │  - State Management (useState, useEffect)            │   │
│  │  - HTTP Client (fetch API)                           │   │
│  └──────────────────┬──────────────────────────────────┘   │
└─────────────────────┼──────────────────────────────────────┘
                      │ HTTP/REST API
                      │ (JSON)
┌─────────────────────▼──────────────────────────────────────┐
│                   FastAPI Backend                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Layer (main.py)                                  │  │
│  │  - Endpoints: /api/match, /api/jobs/{id}, etc.      │  │
│  │  - CORS, Validation, Error Handling                  │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │  Business Logic                                       │  │
│  │  - ContractorMatcher Class                           │  │
│  │  - Matching Algorithm                                │  │
│  │  - Progress Tracking                                 │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │  Data Layer                                           │  │
│  │  - File I/O (Pandas)                                 │  │
│  │  - In-Memory Job Store (Dict)                       │  │
│  │  - Excel Generation                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Backend Architecture

### Technology Stack

- **Framework**: FastAPI 0.104+
- **Data Processing**: Pandas 2.1+
- **String Matching**: RapidFuzz 3.5+
- **ASGI Server**: Uvicorn 0.24+
- **Validation**: Pydantic 2.5+
- **Excel I/O**: OpenPyXL 3.1+

### Core Components

#### 1. API Layer (`main.py`)

**Responsibilities**:
- HTTP request/response handling
- File upload processing
- CORS middleware
- Background task management
- Error handling

**Key Endpoints**:
```python
@app.get("/")                           # Health check
@app.post("/api/match")                 # Create job
@app.get("/api/jobs/{job_id}")         # Get status
@app.get("/api/jobs/{job_id}/download") # Download results
@app.get("/api/jobs")                  # List all jobs
```

#### 2. Matching Engine (`ContractorMatcher`)

**Responsibilities**:
- Data preprocessing and cleaning
- Building search indexes
- Fuzzy string matching
- Candidate filtering
- Match scoring
- Action determination

**Key Methods**:
```python
class ContractorMatcher:
    def __init__(config: MatchConfig)
    def clean_company_name(name: str) -> str
    def build_cbx_index(cbx_df: DataFrame)
    def get_candidate_matches(hc_row: Series) -> List[int]
    def calculate_match_score(hc_row: Series, cbx_row: Series) -> Dict
    def determine_action(hc_row: Series, match_data: Dict) -> str
    def match_contractors(hc_df: DataFrame) -> DataFrame
```

#### 3. Background Processing

**Async Task Runner**:
```python
async def process_matching_job(
    job_id: str,
    cbx_file: Path,
    hc_file: Path,
    config: MatchConfig
)
```

**Job Lifecycle**:
1. File upload → Save to `uploads/`
2. Create job record → Store in `jobs` dict
3. Background task starts
4. Read files (CSV/Excel)
5. Build indexes
6. Process matches with progress updates
7. Generate Excel output
8. Update job status to "completed"

### Data Flow

```
1. File Upload
   └─> MultipartForm → save to uploads/ → return job_id

2. Job Processing (Background)
   └─> Read files
       └─> Pandas DataFrame
           └─> Build Indexes
               └─> For each HC record:
                   └─> Get candidates (pre-filtering)
                       └─> Score candidates
                           └─> Filter by thresholds
                               └─> Pick best match
                                   └─> Determine action
                                       └─> Update progress
                                           └─> Return results

3. Progress Tracking
   └─> Job dict updated in-memory
       └─> Frontend polls every 1s
           └─> GET /api/jobs/{id}
               └─> Return current progress

4. Result Generation
   └─> DataFrame → Excel file
       └─> Multiple sheets by action
           └─> Save to outputs/
               └─> Mark job completed

5. Download
   └─> GET /api/jobs/{id}/download
       └─> Stream file to browser
```

---

## ⚛️ Frontend Architecture

### Technology Stack

- **Framework**: React 18
- **Build Tool**: Vite 5.0
- **Styling**: Tailwind CSS 3.4
- **Icons**: Lucide React
- **HTTP**: Native Fetch API

### Component Structure

```
App.jsx (Main Component)
├─ State Management
│  ├─ File states (cbxFile, hcFile)
│  ├─ Job states (jobId, jobStatus, loading)
│  ├─ UI states (activeTab, logs, error)
│  └─ Dashboard states (jobHistory, stats)
│
├─ Effects (useEffect)
│  ├─ Load job history from localStorage
│  ├─ Timer (elapsed time tracking)
│  ├─ Auto-scroll terminal
│  └─ Stats calculation
│
├─ Functions
│  ├─ File handling (handleFileChange)
│  ├─ Form submission (handleSubmit)
│  ├─ Job polling (pollJobStatus)
│  ├─ Result download (handleDownload)
│  └─ Logging (addLog)
│
└─ UI Components
   ├─ Header & Stats Cards
   ├─ Tab Navigation (Upload, History, Logs)
   ├─ Upload Form
   │  ├─ File Upload Areas
   │  ├─ Threshold Sliders
   │  └─ Submit Button
   ├─ Processing View
   │  ├─ Status Icon
   │  ├─ Progress Bar
   │  ├─ Timer Display
   │  ├─ Record Counter
   │  └─ Job Details
   ├─ History View
   │  ├─ Search & Filter
   │  └─ Job Cards
   ├─ Logs View
   │  └─ Log Cards
   └─ Live Console (Terminal)
```

### State Management

**React Hooks Used**:
- `useState` - Component state
- `useEffect` - Side effects (timers, loading)
- `useCallback` - Memoized functions
- `useRef` - DOM references (terminal scroll)

**State Flow**:
```javascript
// File Selection
User clicks → handleFileChange → setCbxFile/setHcFile → UI updates

// Form Submit
User clicks "Start" → handleSubmit → 
  → setLoading(true)
  → POST /api/match
  → setJobId(id)
  → pollJobStatus(id)

// Polling Loop
pollJobStatus → 
  → GET /api/jobs/{id}
  → setJobStatus(data)
  → if processing → setTimeout(poll, 1000)
  → if complete → enable download

// Download
User clicks → handleDownload →
  → GET /api/jobs/{id}/download
  → Browser downloads file
```

### Data Persistence

**localStorage**:
- Job history (last 50 jobs)
- Statistics (total jobs, success rate, etc.)

**Structure**:
```javascript
{
  jobHistory: [
    {
      id: "uuid",
      status: "completed",
      createdAt: "2025-11-18T14:32:15",
      recordsProcessed: 100,
      duration: 125 // seconds
    }
  ]
}
```

---

## 🧮 Matching Algorithm

### Overview

The matching algorithm uses a **multi-stage filtering and scoring** approach:

1. **Pre-filtering** (Candidate Selection)
2. **Scoring** (Fuzzy Matching)
3. **Filtering** (Threshold Application)
4. **Ranking** (Best Match Selection)
5. **Action Determination**

### Stage 1: Pre-filtering

**Goal**: Reduce search space from thousands to tens of candidates.

**Techniques**:
- Email domain indexing
- Company name keyword indexing
- Hash-based lookups

**Code**:
```python
def get_candidate_matches(self, hc_row: pd.Series) -> List[int]:
    candidates = set()
    
    # Email/domain matching
    email = normalize_email(hc_row['contact_email'])
    domain = get_domain(email)
    
    if is_generic_domain(domain):
        # Exact email only for Gmail, Yahoo, etc.
        if email in email_index:
            candidates.add(email_index[email])
    else:
        # All contractors with same corporate domain
        candidates.update(domain_index[domain])
    
    # Company name keywords
    keywords = extract_keywords(hc_row['contractor_name'])
    for keyword in keywords:
        candidates.update(company_index[keyword])
    
    return list(candidates)
```

**Performance**: O(1) average case, O(k) worst case (k = candidates)

### Stage 2: Scoring

**Goal**: Calculate match scores for each candidate.

**Scoring Components**:

1. **Company Name Score** (0-100)
   - Uses RapidFuzz `token_sort_ratio`
   - Checks English name, French name, old names
   - Takes maximum score

2. **Address Score** (0-100)
   - Postal code exact match (weighted high)
   - Address fuzzy match
   - Country must match

3. **Contact Match** (Boolean)
   - Email domain match (corporate)
   - Exact email match (personal)

4. **Relationship Match** (Boolean)
   - Check if hiring client is in contractor's client list

**Code**:
```python
def calculate_match_score(self, hc_row, cbx_row):
    # Company name
    ratio_company = max(
        fuzz.token_sort_ratio(cbx_row['name_en'], hc_row['contractor_name']),
        fuzz.token_sort_ratio(cbx_row['name_fr'], hc_row['contractor_name'])
    )
    
    # Address
    ratio_zip = fuzz.ratio(cbx_row['postal_code'], hc_row['postal_code'])
    ratio_address = fuzz.token_sort_ratio(cbx_row['address'], hc_row['address'])
    ratio_address = ratio_address * ratio_zip / 100  # Combined score
    
    # Contact
    contact_match = (
        get_domain(cbx_row['email']) == get_domain(hc_row['contact_email'])
    )
    
    # Relationship
    is_in_relationship = (
        hc_row['hiring_client_name'] in cbx_row['hiring_client_names']
    )
    
    return {
        'ratio_company': ratio_company,
        'ratio_address': ratio_address,
        'contact_match': contact_match,
        'is_in_relationship': is_in_relationship
    }
```

### Stage 3: Filtering

**Goal**: Remove low-quality matches.

**Criteria**:
```python
if (score['contact_match'] or  # Email match OR
    (score['ratio_company'] >= 80 and  # Good company match AND
     score['ratio_address'] >= 80)):    # Good address match
    matches.append(score)
```

### Stage 4: Ranking

**Goal**: Pick the single best match.

**Ranking Order** (priority):
1. Is in hiring client relationship (highest)
2. Has Active status
3. Number of hiring clients (more = more established)
4. Company name match score
5. Address match score

**Code**:
```python
matches.sort(key=lambda x: (
    x['is_in_relationship'],      # Boolean (True > False)
    x['cbx_status'] == 'Active',  # Boolean
    x['hiring_client_count'],     # Integer
    x['ratio_company'],           # 0-100
    x['ratio_address']            # 0-100
), reverse=True)

best_match = matches[0] if matches else None
```

### Stage 5: Action Determination

**Goal**: Decide what to do with the match.

**Decision Tree**:
```
No match?
├─ Yes → Ambiguous? → Yes → ambiguous_onboarding
│                   → No  → onboarding
└─ No → Is Takeover?
        ├─ Yes → Status?
        │        ├─ Suspended → restore_suspended
        │        ├─ Active → add_questionnaire
        │        └─ Other → activation_link
        └─ No → Status?
                ├─ Active → In Relationship?
                │           ├─ Yes → already_qualified
                │           └─ No → add_questionnaire
                ├─ Suspended → restore_suspended
                └─ Other → re_onboarding
```

### Performance Analysis

**Time Complexity**:
- Pre-filtering: O(1) per record
- Scoring: O(k) per record (k = candidates, typically 10-50)
- Total: O(n*k) where n = HC records

**Space Complexity**:
- Indexes: O(m) where m = CBX records
- Results: O(n) where n = HC records

**Typical Performance**:
- 100 HC records × 1,000 CBX records = ~30 seconds
- 1,000 HC records × 10,000 CBX records = ~5 minutes

---

## 🔄 Progress Tracking

### Implementation

**Backend**:
```python
def update_progress(progress_idx):
    progress = progress_idx / total_hc  # Float 0.0-1.0
    jobs[job_id]['progress'] = progress
    jobs[job_id]['message'] = f'Matching contractors... ({progress_idx}/{total_hc})'
    logger.info(f"Progress: {progress:.2%}")

# Called for each record
for idx, hc_row in hc_df.iterrows():
    update_progress(idx + 1)
    # ... matching logic
```

**Frontend**:
```javascript
// Poll every second
async function pollJobStatus(jobId) {
    const response = await fetch(`/api/jobs/${jobId}`);
    const data = await response.json();
    
    setJobStatus(data);  // progress: 0.0-1.0
    
    if (data.status === 'processing') {
        setTimeout(() => pollJobStatus(jobId), 1000);
    }
}

// Display progress bar
<div style={{ width: `${jobStatus.progress * 100}%` }}>
    {Math.round(jobStatus.progress * 100)}%
</div>
```

### Accuracy

- **Updates**: Every record (100% accurate)
- **Granularity**: 1 record = 1/total progress
- **Latency**: ~1 second (polling interval)

---

## 🗄️ Data Storage

### File System Structure

```
backend/
├── uploads/           # Temporary uploaded files
│   ├── {job_id}_cbx.xlsx
│   └── {job_id}_hc.csv
└── outputs/           # Generated result files
    └── {job_id}_results.xlsx
```

### In-Memory Storage

**Jobs Dictionary**:
```python
jobs: Dict[str, Dict[str, Any]] = {
    "job_id_1": {
        "job_id": "...",
        "status": "completed",
        "progress": 1.0,
        "message": "...",
        "result_file": "...",
        "error": None,
        "created_at": "...",
        "completed_at": "..."
    }
}
```

**Limitations**:
- ⚠️ Data lost on server restart
- ⚠️ Not suitable for production at scale
- ⚠️ No persistence across restarts

**Production Alternative**:
- Use Redis for job storage
- Use PostgreSQL for job history
- Use S3/object storage for files

---

## 🔐 Security Considerations

### Current State (Development)

❌ **Not Implemented**:
- Authentication
- Authorization
- Rate limiting
- File size limits
- Input validation (beyond basic)
- HTTPS/SSL
- API keys

### Production Requirements

✅ **Must Implement**:

1. **Authentication**:
   ```python
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   @app.post("/api/match")
   async def create_job(token: str = Depends(security)):
       # Verify token
   ```

2. **File Size Limits**:
   ```python
   @app.post("/api/match")
   async def create_job(
       cbx_file: UploadFile = File(..., max_length=100_000_000)  # 100MB
   ):
   ```

3. **Input Validation**:
   ```python
   class MatchRequest(BaseModel):
       min_company_ratio: int = Field(ge=0, le=100)
       min_address_ratio: int = Field(ge=0, le=100)
   ```

4. **Rate Limiting**:
   ```python
   from slowapi import Limiter
   
   limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/api/match")
   @limiter.limit("5/minute")
   async def create_job():
   ```

5. **CORS**:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://yourdomain.com"],  # Specific domain
       allow_credentials=True,
       allow_methods=["GET", "POST"],  # Specific methods
       allow_headers=["Authorization", "Content-Type"],
   )
   ```

---

## 🧪 Testing

### Unit Tests

**Backend** (`pytest`):
```python
def test_clean_company_name():
    matcher = ContractorMatcher(config)
    result = matcher.clean_company_name("ABC Inc.")
    assert result == "abc"

def test_calculate_match_score():
    score = matcher.calculate_match_score(hc_row, cbx_row)
    assert 0 <= score['ratio_company'] <= 100
```

**Frontend** (`Jest + React Testing Library`):
```javascript
test('file upload updates state', () => {
    const { getByText } = render(<App />);
    const input = getByText('CBX Database File');
    fireEvent.change(input, { target: { files: [file] } });
    expect(cbxFile).toBeTruthy();
});
```

### Integration Tests

```python
def test_full_workflow():
    # Create job
    response = client.post("/api/match", files=files)
    job_id = response.json()['job_id']
    
    # Wait for completion
    while True:
        response = client.get(f"/api/jobs/{job_id}")
        if response.json()['status'] == 'completed':
            break
        time.sleep(1)
    
    # Download results
    response = client.get(f"/api/jobs/{job_id}/download")
    assert response.status_code == 200
```

### Load Testing

**Using Locust**:
```python
from locust import HttpUser, task

class MatchUser(HttpUser):
    @task
    def create_job(self):
        files = {'cbx_file': open('test.xlsx', 'rb')}
        self.client.post("/api/match", files=files)
```

---

## 📊 Performance Optimization

### Backend Optimizations

1. **Indexing** - Pre-build search indexes
2. **Vectorization** - Use Pandas operations instead of loops
3. **Caching** - Cache cleaned names and domains
4. **Async I/O** - Use async file operations
5. **Parallel Processing** - Use multiprocessing for large datasets

### Frontend Optimizations

1. **Code Splitting** - Lazy load components
2. **Memoization** - Use `useMemo` for expensive computations
3. **Virtual Scrolling** - For large history lists
4. **Debouncing** - For search inputs
5. **Service Workers** - Cache assets

---

## 🚀 Deployment

### Docker Setup

**Dockerfile (Backend)**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dockerfile (Frontend)**:
```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
EXPOSE 80
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/outputs:/app/outputs
  
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

### Production Checklist

- [ ] Environment variables configured
- [ ] HTTPS/SSL enabled
- [ ] Authentication implemented
- [ ] Rate limiting enabled
- [ ] Error tracking (Sentry)
- [ ] Logging infrastructure
- [ ] Database for persistence
- [ ] File cleanup cron job
- [ ] Monitoring (Prometheus/Grafana)
- [ ] Backup strategy
- [ ] CI/CD pipeline

---

**Version**: 2.0.0  
**Last Updated**: November 18, 2025

