#!/usr/bin/env python3
"""
Quick verification script to test the new backend
"""
import requests
import time
import sys
from pathlib import Path

API_URL = "http://localhost:8000"

def test_health():
    print("1. Testing health endpoint...")
    try:
        r = requests.get(f"{API_URL}/api/health", timeout=5)
        if r.status_code == 200:
            print(f"   ✓ Backend is healthy: {r.json()}")
            return True
        else:
            print(f"   ✗ Health check failed: {r.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Cannot connect to backend: {e}")
        print(f"   Make sure backend is running: python3 main.py")
        return False

def test_upload(cbx_file, hc_file):
    print(f"\n2. Testing file upload...")
    print(f"   CBX: {cbx_file}")
    print(f"   HC: {hc_file}")

    if not Path(cbx_file).exists():
        print(f"   ✗ CBX file not found: {cbx_file}")
        return None
    if not Path(hc_file).exists():
        print(f"   ✗ HC file not found: {hc_file}")
        return None

    try:
        files = {
            'cbx_file': open(cbx_file, 'rb'),
            'hc_file': open(hc_file, 'rb')
        }
        data = {
            'min_company_ratio': 80,
            'min_address_ratio': 80
        }

        r = requests.post(f"{API_URL}/api/match", files=files, data=data, timeout=30)

        if r.status_code == 200:
            job = r.json()
            print(f"   ✓ Job created: {job['job_id']}")
            return job['job_id']
        else:
            print(f"   ✗ Upload failed: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"   ✗ Upload error: {e}")
        return None

def test_progress(job_id):
    print(f"\n3. Monitoring job progress...")

    start_time = time.time()
    last_progress = -1

    while True:
        try:
            r = requests.get(f"{API_URL}/api/jobs/{job_id}", timeout=5)
            if r.status_code == 200:
                job = r.json()
                progress = job['progress']
                status = job['status']
                message = job['message']

                if progress != last_progress:
                    elapsed = time.time() - start_time
                    print(f"   [{elapsed:6.1f}s] {progress*100:5.1f}% - {status:12} - {message}")
                    last_progress = progress

                if status == "completed":
                    print(f"\n   ✓ Job completed successfully!")
                    print(f"   Result file: {job['result_file']}")
                    return True
                elif status == "failed":
                    print(f"\n   ✗ Job failed: {job.get('error', 'Unknown error')}")
                    return False

                time.sleep(2)
            else:
                print(f"   ✗ Status check failed: {r.status_code}")
                return False
        except KeyboardInterrupt:
            print("\n   Interrupted by user")
            return False
        except Exception as e:
            print(f"   ✗ Error checking status: {e}")
            return False

def main():
    print("=" * 60)
    print("  Onboarding Analysis Tool - Backend Verification")
    print("=" * 60)
    print()

    # Test health
    if not test_health():
        sys.exit(1)

    # Find test files
    test_data = Path("testdata")
    data_dir = Path("data")

    cbx_file = None
    hc_file = None

    # Try testdata first
    if test_data.exists():
        cbx_candidates = list(test_data.glob("*cbx*.csv")) + list(test_data.glob("*cbx*.xlsx"))
        hc_candidates = list(test_data.glob("*hc*.csv")) + list(test_data.glob("*hc*.xlsx"))
        if cbx_candidates:
            cbx_file = cbx_candidates[0]
        if hc_candidates:
            hc_file = hc_candidates[0]

    # Try data dir
    if not cbx_file and data_dir.exists():
        cbx_candidates = list(data_dir.glob("*cbx*.csv")) + list(data_dir.glob("*cbx*.xlsx"))
        hc_candidates = list(data_dir.glob("*hc*.csv")) + list(data_dir.glob("*hc*.xlsx"))
        if cbx_candidates:
            cbx_file = cbx_candidates[0]
        if hc_candidates:
            hc_file = hc_candidates[0]

    # Allow command line args
    if len(sys.argv) >= 3:
        cbx_file = Path(sys.argv[1])
        hc_file = Path(sys.argv[2])

    if not cbx_file or not hc_file:
        print("\nUsage:")
        print(f"  {sys.argv[0]} <cbx_file> <hc_file>")
        print(f"\nOr place test files in testdata/ or data/ directory")
        sys.exit(1)

    # Test upload
    job_id = test_upload(cbx_file, hc_file)
    if not job_id:
        sys.exit(1)

    # Monitor progress
    success = test_progress(job_id)

    print()
    print("=" * 60)
    if success:
        print("  ✓ ALL TESTS PASSED")
        print(f"  Download: http://localhost:8000/api/jobs/{job_id}/download")
    else:
        print("  ✗ TESTS FAILED")
    print("=" * 60)
    print()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

