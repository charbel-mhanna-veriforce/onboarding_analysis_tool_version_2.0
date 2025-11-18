#!/usr/bin/env python3
"""
Test script to verify progress tracking is working
"""
import time
import requests
import json

API_URL = "http://localhost:8000"

def test_progress():
    print("=" * 60)
    print("Testing Backend Progress Tracking")
    print("=" * 60)

    # Check if server is running
    try:
        response = requests.get(f"{API_URL}/")
        print(f"✓ Server is running: {response.json()}")
    except Exception as e:
        print(f"✗ Server not accessible: {e}")
        return

    # List existing jobs
    try:
        response = requests.get(f"{API_URL}/api/jobs")
        jobs = response.json().get('jobs', [])
        print(f"\n✓ Found {len(jobs)} existing jobs")

        if jobs:
            # Monitor the most recent job
            recent_job = jobs[0]
            job_id = recent_job['job_id']
            print(f"\nMonitoring recent job: {job_id}")
            print("-" * 60)

            for i in range(30):  # Monitor for 30 seconds
                response = requests.get(f"{API_URL}/api/jobs/{job_id}")
                data = response.json()

                progress_pct = round(data.get('progress', 0) * 100, 1)
                status = data.get('status', 'unknown')
                message = data.get('message', 'No message')

                print(f"[{i+1:2d}s] Status: {status:12s} | Progress: {progress_pct:5.1f}% | {message}")

                if status in ['completed', 'failed']:
                    print(f"\n✓ Job finished with status: {status}")
                    if status == 'completed':
                        print(f"  Result file: {data.get('result_file')}")
                    elif status == 'failed':
                        print(f"  Error: {data.get('error')}")
                    break

                time.sleep(1)

            print("-" * 60)
        else:
            print("  No jobs to monitor. Upload files to create a job.")

    except Exception as e:
        print(f"✗ Error accessing jobs: {e}")

if __name__ == "__main__":
    test_progress()

