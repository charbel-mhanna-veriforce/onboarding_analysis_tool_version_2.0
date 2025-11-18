#!/usr/bin/env python3
"""
Debug script to test if background tasks are working
"""
import requests
import time
import sys

API_URL = "http://localhost:8000"

def test_api():
    print("=" * 60)
    print("Testing API and Background Tasks")
    print("=" * 60)

    # Test 1: Check if server is running
    print("\n1. Testing server connection...")
    try:
        response = requests.get(f"{API_URL}/")
        print(f"   ✓ Server is running: {response.json()}")
    except Exception as e:
        print(f"   ✗ Cannot connect to server: {e}")
        print("\n   Please start the backend server first:")
        print("   cd backend && python3 main.py")
        return False

    # Test 2: Check uploads directory exists
    print("\n2. Checking uploads directory...")
    import os
    if os.path.exists('uploads'):
        print(f"   ✓ uploads/ directory exists")
    else:
        print(f"   ✗ uploads/ directory missing")
        os.makedirs('uploads', exist_ok=True)
        print(f"   ✓ Created uploads/ directory")

    # Test 3: List current jobs
    print("\n3. Checking for existing jobs...")
    try:
        response = requests.get(f"{API_URL}/api/jobs")
        jobs = response.json().get('jobs', [])
        print(f"   ✓ Found {len(jobs)} existing jobs")
        for job in jobs[:3]:  # Show first 3
            print(f"      - {job['job_id']}: {job['status']} ({job['progress']*100:.1f}%)")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Diagnosis:")
    print("=" * 60)
    print("\nIf you don't see the '!!!! BACKGROUND TASK STARTED' log")
    print("when you upload files, it means:")
    print("1. Files aren't uploading properly")
    print("2. Background task isn't being scheduled")
    print("3. FastAPI BackgroundTasks isn't working")
    print("\nWatch the backend terminal for these logs:")
    print("  - 'CBX file saved: ...'")
    print("  - 'HC file saved: ...'")
    print("  - 'Scheduling background task for job ...'")
    print("  - '!!!! BACKGROUND TASK STARTED FOR JOB ...'")
    print("\nIf you see 'Scheduling' but NOT 'BACKGROUND TASK STARTED',")
    print("then FastAPI's background tasks aren't executing.")
    print("\nTry restarting the backend server.")

    return True

if __name__ == "__main__":
    test_api()

