"""
ULTRA-FAST Backend - with detailed timing logs
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import pandas as pd
from datetime import datetime
import uuid
import shutil
from pathlib import Path
import logging
from rapidfuzz import fuzz
import re
from collections import defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

jobs: Dict[str, Dict[str, Any]] = {}

def update_job(job_id: str, **kwargs):
    if job_id in jobs:
        jobs[job_id].update(kwargs)

GENERIC_DOMAINS = {'yahoo.ca', 'yahoo.com', 'hotmail.com', 'gmail.com', 'outlook.com'}
GENERIC_WORDS = {'construction', 'contracting', 'service', 'services', 'inc', 'ltd'}

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str
    result_file: Optional[str] = None
    error: Optional[str] = None
    created_at: str

class MatchConfig(BaseModel):
    min_company_ratio: int = 80
    min_address_ratio: int = 80

class ContractorMatcher:
    def __init__(self, config: MatchConfig):
        self.config = config
        self.cbx_data = None

    def clean_company_name(self, name: str) -> str:
        if not name or pd.isna(name):
            return ""
        name = str(name).lower().strip()
        name = re.sub(r'[.,()]', '', name)
        for word in GENERIC_WORDS:
            name = re.sub(r'\b' + re.escape(word) + r'\b', '', name)
        return ' '.join(name.split())

    def normalize_email(self, email: str) -> str:
        if not email or pd.isna(email):
            return ""
        return str(email).lower().strip().split(';')[0].split(',')[0].strip()

    def get_domain(self, email: str) -> str:
        return email.split('@')[1] if '@' in email else ""

    def is_generic_domain(self, domain: str) -> bool:
        return domain in GENERIC_DOMAINS

    def build_cbx_index(self, cbx_df: pd.DataFrame):
        self.cbx_data = cbx_df
        self.domain_index = defaultdict(list)
        self.email_index = {}
        self.company_index = defaultdict(list)

        for idx, row in cbx_df.iterrows():
            email = self.normalize_email(row.get('email', ''))
            if email:
                domain = self.get_domain(email)
                self.email_index[email] = idx
                if not self.is_generic_domain(domain):
                    self.domain_index[domain].append(idx)

            clean_name = self.clean_company_name(row.get('name_en', ''))
            if clean_name:
                for word in clean_name.split()[:3]:
                    if len(word) > 3:
                        self.company_index[word].append(idx)

    def match_contractors(self, hc_df: pd.DataFrame, progress_callback=None):
        results = []
        total = len(hc_df)

        for idx, (_, hc_row) in enumerate(hc_df.iterrows()):
            if progress_callback and idx % 10 == 0:
                progress_callback(idx + 1)

            # Get candidates
            candidates = set()
            email = self.normalize_email(hc_row.get('contact_email', ''))
            if email:
                domain = self.get_domain(email)
                if self.is_generic_domain(domain):
                    if email in self.email_index:
                        candidates.add(self.email_index[email])
                else:
                    candidates.update(self.domain_index.get(domain, []))

            clean_name = self.clean_company_name(hc_row.get('contractor_name', ''))
            for word in clean_name.split()[:3]:
                if len(word) > 3:
                    candidates.update(self.company_index.get(word, []))

            if not candidates:
                candidates = set(range(len(self.cbx_data)))

            # Score matches
            matches = []
            for cbx_idx in candidates:
                cbx_row = self.cbx_data.iloc[cbx_idx]

                hc_company = self.clean_company_name(hc_row.get('contractor_name', ''))
                cbx_company = self.clean_company_name(cbx_row.get('name_en', ''))
                ratio_company = fuzz.token_sort_ratio(cbx_company, hc_company)

                if ratio_company >= self.config.min_company_ratio:
                    matches.append({
                        'cbx_id': cbx_row.get('id'),
                        'cbx_company': cbx_row.get('name_en'),
                        'ratio_company': ratio_company
                    })

            # Build result
            result = hc_row.to_dict()
            result['match_count'] = len(matches)
            result['action'] = 'onboarding' if not matches else 'add_questionnaire'

            if matches:
                best = max(matches, key=lambda x: x['ratio_company'])
                result['matched_cbx_id'] = best['cbx_id']
                result['matched_company'] = best['cbx_company']
                result['match_ratio'] = best['ratio_company']

            results.append(result)

        return pd.DataFrame(results)


EXECUTOR = ThreadPoolExecutor(max_workers=2)

def process_job(job_id: str, cbx_path: Path, hc_path: Path, config: MatchConfig):
    try:
        t0 = time.time()
        logger.info(f"[{job_id}] Starting processing")

        update_job(job_id, status='processing', message='Reading CBX...', progress=0.05)
        t1 = time.time()
        cbx_df = pd.read_excel(cbx_path, engine='openpyxl') if cbx_path.suffix == '.xlsx' else pd.read_csv(cbx_path)
        logger.info(f"[{job_id}] CBX read in {time.time()-t1:.2f}s ({len(cbx_df)} rows)")

        update_job(job_id, message='Reading HC...', progress=0.10)
        t1 = time.time()
        hc_df = pd.read_excel(hc_path, engine='openpyxl') if hc_path.suffix == '.xlsx' else pd.read_csv(hc_path)
        logger.info(f"[{job_id}] HC read in {time.time()-t1:.2f}s ({len(hc_df)} rows)")

        update_job(job_id, message='Building index...', progress=0.15)
        t1 = time.time()
        matcher = ContractorMatcher(config)
        matcher.build_cbx_index(cbx_df.dropna(how='all'))
        logger.info(f"[{job_id}] Index built in {time.time()-t1:.2f}s")

        total = len(hc_df)
        update_job(job_id, message=f'Matching {total} records...', progress=0.20)

        def progress_cb(idx):
            p = 0.20 + 0.70 * (idx / total)
            update_job(job_id, progress=p, message=f'{idx}/{total}')

        t1 = time.time()
        results = matcher.match_contractors(hc_df.dropna(how='all'), progress_cb)
        logger.info(f"[{job_id}] Matching done in {time.time()-t1:.2f}s")

        update_job(job_id, progress=0.95, message='Saving...')
        t1 = time.time()
        out_file = OUTPUT_DIR / f'{job_id}_results.xlsx'
        with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
            results.to_excel(writer, sheet_name='Results', index=False)
        logger.info(f"[{job_id}] Saved in {time.time()-t1:.2f}s")

        logger.info(f"[{job_id}] TOTAL TIME: {time.time()-t0:.2f}s")
        update_job(job_id, status='completed', progress=1.0, message='Done!', result_file=out_file.name)

    except Exception as e:
        logger.exception(f'[{job_id}] FAILED')
        update_job(job_id, status='failed', message=str(e), error=str(e))


@app.post("/api/match", response_model=JobStatus)
async def match(
    cbx_file: UploadFile = File(...),
    hc_file: UploadFile = File(...),
    min_company_ratio: int = Form(80),
    min_address_ratio: int = Form(80)
):
    """Ultra-fast upload"""
    t_start = time.time()
    logger.info(f"========== NEW REQUEST ==========")
    logger.info(f"Files: {cbx_file.filename}, {hc_file.filename}")

    job_id = str(uuid.uuid4())[:8]  # Shorter ID for logs

    cbx_path = UPLOAD_DIR / f"{job_id}_cbx.{cbx_file.filename.split('.')[-1]}"
    hc_path = UPLOAD_DIR / f"{job_id}_hc.{hc_file.filename.split('.')[-1]}"

    # Method 1: Use shutil (FASTEST)
    logger.info(f"Saving CBX...")
    t1 = time.time()
    with open(cbx_path, 'wb') as f:
        shutil.copyfileobj(cbx_file.file, f, length=1024*1024)  # 1MB chunks
    logger.info(f"CBX saved in {time.time()-t1:.3f}s ({cbx_path.stat().st_size/1024/1024:.2f} MB)")

    logger.info(f"Saving HC...")
    t1 = time.time()
    with open(hc_path, 'wb') as f:
        shutil.copyfileobj(hc_file.file, f, length=1024*1024)
    logger.info(f"HC saved in {time.time()-t1:.3f}s ({hc_path.stat().st_size/1024/1024:.2f} MB)")

    logger.info(f"TOTAL UPLOAD TIME: {time.time()-t_start:.3f}s")

    # Create job
    jobs[job_id] = {
        'job_id': job_id,
        'status': 'processing',
        'progress': 0.01,
        'message': 'Starting...',
        'created_at': datetime.now().isoformat(),
        'result_file': None,
        'error': None
    }

    # Start processing
    config = MatchConfig(min_company_ratio=min_company_ratio, min_address_ratio=min_address_ratio)
    loop = asyncio.get_running_loop()
    loop.run_in_executor(EXECUTOR, process_job, job_id, cbx_path, hc_path, config)

    return JobStatus(**jobs[job_id])


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    return JobStatus(**jobs[job_id])


@app.get("/api/jobs/{job_id}/download")
async def download(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404)
    job = jobs[job_id]
    if job['status'] != 'completed':
        raise HTTPException(400, "Not completed")
    file_path = OUTPUT_DIR / job['result_file']
    return FileResponse(file_path, filename=job['result_file'])


@app.get("/api/jobs")
async def list_jobs():
    return {"jobs": list(jobs.values())}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")