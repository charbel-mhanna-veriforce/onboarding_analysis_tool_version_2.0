# API Documentation

## 📡 Overview

The Onboarding Analysis Tool backend provides a RESTful API built with FastAPI. This document covers all available endpoints, request/response formats, and usage examples.

**Base URL**: `http://localhost:8000`

---

## 🔗 Endpoints

### 1. Root Endpoint

**GET** `/`

Health check and API information.

**Response**:
```json
{
  "name": "Contractor Matching API",
  "version": "2.0.0",
  "status": "running"
}
```

**Example**:
```bash
curl http://localhost:8000/
```

---

### 2. Create Matching Job

**POST** `/api/match`

Upload files and create a new matching job.

**Request**:
- **Content-Type**: `multipart/form-data`
- **Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cbx_file` | File | Yes | CBX database file (.csv, .xlsx, .xls) |
| `hc_file` | File | Yes | Hiring client file (.csv, .xlsx, .xls) |
| `min_company_ratio` | int | No | Company name match threshold (0-100, default: 80) |
| `min_address_ratio` | int | No | Address match threshold (0-100, default: 80) |

**Response** (200 OK):
```json
{
  "job_id": "696ec873-2f69-4543-9689-110ff6fe9d3b",
  "status": "pending",
  "progress": 0.0,
  "message": "Job queued",
  "result_file": null,
  "error": null,
  "created_at": "2025-11-18T14:32:15.123456",
  "completed_at": null
}
```

**Error Responses**:

*400 Bad Request*:
```json
{
  "detail": "CBX file must be CSV, XLSX, or XLS format"
}
```

**Example (cURL)**:
```bash
curl -X POST http://localhost:8000/api/match \
  -F "cbx_file=@contractors.xlsx" \
  -F "hc_file=@submissions.csv" \
  -F "min_company_ratio=85" \
  -F "min_address_ratio=80"
```

**Example (JavaScript)**:
```javascript
const formData = new FormData();
formData.append('cbx_file', cbxFile);
formData.append('hc_file', hcFile);
formData.append('min_company_ratio', 80);
formData.append('min_address_ratio', 80);

const response = await fetch('http://localhost:8000/api/match', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log('Job ID:', data.job_id);
```

**Example (Python)**:
```python
import requests

files = {
    'cbx_file': open('contractors.xlsx', 'rb'),
    'hc_file': open('submissions.csv', 'rb')
}

data = {
    'min_company_ratio': 80,
    'min_address_ratio': 80
}

response = requests.post(
    'http://localhost:8000/api/match',
    files=files,
    data=data
)

job = response.json()
print(f"Job ID: {job['job_id']}")
```

---

### 3. Get Job Status

**GET** `/api/jobs/{job_id}`

Get the current status of a job.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string | UUID of the job |

**Response** (200 OK):

*Pending/Processing*:
```json
{
  "job_id": "696ec873-2f69-4543-9689-110ff6fe9d3b",
  "status": "processing",
  "progress": 0.45,
  "message": "Matching contractors... (45/100)",
  "result_file": null,
  "error": null,
  "created_at": "2025-11-18T14:32:15.123456",
  "completed_at": null
}
```

*Completed*:
```json
{
  "job_id": "696ec873-2f69-4543-9689-110ff6fe9d3b",
  "status": "completed",
  "progress": 1.0,
  "message": "Processing complete",
  "result_file": "696ec873-2f69-4543-9689-110ff6fe9d3b_results.xlsx",
  "error": null,
  "created_at": "2025-11-18T14:32:15.123456",
  "completed_at": "2025-11-18T14:35:42.789012"
}
```

*Failed*:
```json
{
  "job_id": "696ec873-2f69-4543-9689-110ff6fe9d3b",
  "status": "failed",
  "progress": 0.23,
  "message": "Error: Invalid column name",
  "result_file": null,
  "error": "KeyError: 'contractor_name'",
  "created_at": "2025-11-18T14:32:15.123456",
  "completed_at": null
}
```

**Error Responses**:

*404 Not Found*:
```json
{
  "detail": "Job not found"
}
```

**Example (cURL)**:
```bash
curl http://localhost:8000/api/jobs/696ec873-2f69-4543-9689-110ff6fe9d3b
```

**Example (JavaScript - Polling)**:
```javascript
async function pollJobStatus(jobId) {
  const response = await fetch(`http://localhost:8000/api/jobs/${jobId}`);
  const data = await response.json();
  
  console.log(`Status: ${data.status}, Progress: ${data.progress * 100}%`);
  
  if (data.status === 'processing' || data.status === 'pending') {
    // Poll again in 1 second
    setTimeout(() => pollJobStatus(jobId), 1000);
  } else if (data.status === 'completed') {
    console.log('Job completed!');
    downloadResults(jobId);
  } else if (data.status === 'failed') {
    console.error('Job failed:', data.error);
  }
}
```

**Example (Python)**:
```python
import time
import requests

def wait_for_job(job_id):
    while True:
        response = requests.get(f'http://localhost:8000/api/jobs/{job_id}')
        job = response.json()
        
        print(f"Status: {job['status']}, Progress: {job['progress']*100:.1f}%")
        
        if job['status'] == 'completed':
            return job
        elif job['status'] == 'failed':
            raise Exception(job['error'])
        
        time.sleep(1)
```

---

### 4. Download Results

**GET** `/api/jobs/{job_id}/download`

Download the results file for a completed job.

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | string | UUID of the job |

**Response** (200 OK):
- **Content-Type**: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Content-Disposition**: `attachment; filename="{job_id}_results.xlsx"`
- **Body**: Binary Excel file

**Error Responses**:

*404 Not Found*:
```json
{
  "detail": "Job not found"
}
```

*400 Bad Request*:
```json
{
  "detail": "Job not completed"
}
```

*404 Not Found*:
```json
{
  "detail": "Result file not found"
}
```

**Example (cURL)**:
```bash
curl -O http://localhost:8000/api/jobs/696ec873-2f69-4543-9689-110ff6fe9d3b/download
```

**Example (JavaScript)**:
```javascript
async function downloadResults(jobId) {
  const response = await fetch(
    `http://localhost:8000/api/jobs/${jobId}/download`
  );
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${jobId}_results.xlsx`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}
```

**Example (Python)**:
```python
import requests

def download_results(job_id):
    response = requests.get(
        f'http://localhost:8000/api/jobs/{job_id}/download'
    )
    
    with open(f'{job_id}_results.xlsx', 'wb') as f:
        f.write(response.content)
    
    print(f"Results saved to {job_id}_results.xlsx")
```

---

### 5. List All Jobs

**GET** `/api/jobs`

Get a list of all jobs.

**Response** (200 OK):
```json
{
  "jobs": [
    {
      "job_id": "696ec873-2f69-4543-9689-110ff6fe9d3b",
      "status": "completed",
      "progress": 1.0,
      "message": "Processing complete",
      "result_file": "696ec873-2f69-4543-9689-110ff6fe9d3b_results.xlsx",
      "error": null,
      "created_at": "2025-11-18T14:32:15.123456",
      "completed_at": "2025-11-18T14:35:42.789012"
    },
    {
      "job_id": "abc12345-6789-0def-ghij-klmnopqrstuv",
      "status": "processing",
      "progress": 0.67,
      "message": "Matching contractors... (67/100)",
      "result_file": null,
      "error": null,
      "created_at": "2025-11-18T15:10:22.456789",
      "completed_at": null
    }
  ]
}
```

**Example (cURL)**:
```bash
curl http://localhost:8000/api/jobs
```

**Example (JavaScript)**:
```javascript
async function listJobs() {
  const response = await fetch('http://localhost:8000/api/jobs');
  const data = await response.json();
  
  data.jobs.forEach(job => {
    console.log(`${job.job_id}: ${job.status} - ${job.progress * 100}%`);
  });
}
```

---

## 📊 Data Models

### JobStatus

```typescript
interface JobStatus {
  job_id: string;           // UUID
  status: string;           // "pending" | "processing" | "completed" | "failed"
  progress: number;         // 0.0 to 1.0
  message: string;          // Human-readable status message
  result_file: string | null;  // Filename if completed
  error: string | null;     // Error message if failed
  created_at: string;       // ISO 8601 timestamp
  completed_at: string | null;  // ISO 8601 timestamp
}
```

### MatchConfig

```typescript
interface MatchConfig {
  min_company_ratio: number;   // 0-100, default: 80
  min_address_ratio: number;   // 0-100, default: 80
  use_contact_matching: boolean;  // default: true
  prioritize_active: boolean;  // default: true
}
```

---

## 🔄 Job Lifecycle

```
1. CREATE     → POST /api/match
   ↓
2. PENDING    → status: "pending", progress: 0.0
   ↓
3. PROCESSING → status: "processing", progress: 0.01-0.99
   ↓           (Poll GET /api/jobs/{id} every 1 second)
   ↓
4. COMPLETED  → status: "completed", progress: 1.0
   ↓
5. DOWNLOAD   → GET /api/jobs/{id}/download
```

---

## ⚡ Rate Limits

Currently no rate limits are enforced. For production:
- Recommend: 10 requests/second per IP
- Recommend: 100 jobs/hour per user

---

## 🔒 Authentication

Currently no authentication required. For production:
- Implement API key authentication
- Use JWT tokens for session management
- Add role-based access control (RBAC)

---

## 🐛 Error Handling

### HTTP Status Codes

| Code | Meaning | When It Happens |
|------|---------|-----------------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid file format, missing parameters |
| 404 | Not Found | Job ID doesn't exist |
| 500 | Internal Server Error | Backend error, check logs |

### Error Response Format

All errors follow this format:
```json
{
  "detail": "Human-readable error message"
}
```

### Common Errors

**Invalid File Format**:
```json
{
  "detail": "CBX file must be CSV, XLSX, or XLS format"
}
```

**Missing Required Column**:
```json
{
  "detail": "KeyError: 'contractor_name'"
}
```

**Job Not Found**:
```json
{
  "detail": "Job not found"
}
```

---

## 🧪 Testing the API

### Using cURL

**Full workflow**:
```bash
# 1. Create job
JOB_ID=$(curl -X POST http://localhost:8000/api/match \
  -F "cbx_file=@contractors.xlsx" \
  -F "hc_file=@submissions.csv" \
  | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# 2. Poll status
while true; do
  STATUS=$(curl -s http://localhost:8000/api/jobs/$JOB_ID | jq -r '.status')
  PROGRESS=$(curl -s http://localhost:8000/api/jobs/$JOB_ID | jq -r '.progress')
  echo "Status: $STATUS, Progress: $PROGRESS"
  
  if [ "$STATUS" = "completed" ]; then
    break
  fi
  
  sleep 1
done

# 3. Download results
curl -O http://localhost:8000/api/jobs/$JOB_ID/download
echo "Results downloaded!"
```

### Using Python

```python
import requests
import time

# 1. Create job
files = {
    'cbx_file': open('contractors.xlsx', 'rb'),
    'hc_file': open('submissions.csv', 'rb')
}
response = requests.post('http://localhost:8000/api/match', files=files)
job_id = response.json()['job_id']
print(f"Job created: {job_id}")

# 2. Poll status
while True:
    response = requests.get(f'http://localhost:8000/api/jobs/{job_id}')
    job = response.json()
    
    print(f"Status: {job['status']}, Progress: {job['progress']*100:.1f}%")
    
    if job['status'] == 'completed':
        break
    elif job['status'] == 'failed':
        print(f"Error: {job['error']}")
        exit(1)
    
    time.sleep(1)

# 3. Download results
response = requests.get(f'http://localhost:8000/api/jobs/{job_id}/download')
with open('results.xlsx', 'wb') as f:
    f.write(response.content)

print("Results downloaded!")
```

### Using Postman

1. **Create Job**:
   - Method: POST
   - URL: `http://localhost:8000/api/match`
   - Body: form-data
     - cbx_file: [Select File]
     - hc_file: [Select File]
     - min_company_ratio: 80
     - min_address_ratio: 80

2. **Get Status**:
   - Method: GET
   - URL: `http://localhost:8000/api/jobs/{job_id}`

3. **Download Results**:
   - Method: GET
   - URL: `http://localhost:8000/api/jobs/{job_id}/download`
   - Save Response: To File

---

## 📝 Best Practices

### Polling

1. **Poll every 1 second** during processing
2. **Don't poll faster** - wastes resources
3. **Stop polling** when status is "completed" or "failed"
4. **Handle errors** gracefully

### File Upload

1. **Check file size** before upload (< 100MB recommended)
2. **Validate file format** client-side first
3. **Show progress** during upload (if large files)
4. **Handle upload errors** with retry logic

### Error Handling

1. **Always check status code** before parsing response
2. **Display user-friendly errors** (not raw API errors)
3. **Log errors** for debugging
4. **Retry on network errors** (not on 400 errors)

---

## 🔧 CORS Configuration

The API allows requests from:
- `http://localhost:3000`
- `http://localhost:5173`

For production, update `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📚 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **OpenAPI Spec**: http://localhost:8000/docs (when running)
- **ReDoc**: http://localhost:8000/redoc (when running)

---

**API Version**: 2.0.0  
**Last Updated**: November 18, 2025

