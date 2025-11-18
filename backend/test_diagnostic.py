#!/usr/bin/env python3
"""
Comprehensive test to diagnose backend processing issue
Tests each step of the process to identify where it fails
"""
import os
import sys
import time

def test_backend():
    print("=" * 70)
    print("BACKEND PROCESSING DIAGNOSTIC TEST")
    print("=" * 70)

    # Test 1: Check backend is running
    print("\n[TEST 1] Checking if backend is running...")
    try:
        import urllib.request
        import json

        response = urllib.request.urlopen("http://localhost:8000/")
        data = json.loads(response.read().decode())
        print(f"✓ Backend is running: {data}")
    except Exception as e:
        print(f"✗ Backend NOT running: {e}")
        print("\n  ACTION REQUIRED:")
        print("  1. Open a terminal")
        print("  2. cd /home/dev/onboarding_analysis_tool_version_2.0/backend")
        print("  3. python3 main.py")
        return False

    # Test 2: Check for test files
    print("\n[TEST 2] Checking for uploaded files...")
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        files = os.listdir(uploads_dir)
        print(f"✓ Uploads directory exists with {len(files)} files")
        if files:
            for f in files[:5]:  # Show first 5
                size = os.path.getsize(os.path.join(uploads_dir, f))
                print(f"  - {f} ({size:,} bytes)")
    else:
        print(f"✗ Uploads directory missing")
        os.makedirs(uploads_dir)
        print(f"  Created {uploads_dir}/")

    # Test 3: Check job status endpoint
    print("\n[TEST 3] Testing job status endpoint...")
    try:
        response = urllib.request.urlopen("http://localhost:8000/api/jobs")
        data = json.loads(response.read().decode())
        jobs = data.get('jobs', [])
        print(f"✓ Jobs endpoint working, found {len(jobs)} jobs")

        if jobs:
            print("\n  Recent jobs:")
            for job in jobs[:3]:
                print(f"  - Job {job['job_id'][:8]}...")
                print(f"    Status: {job['status']}")
                print(f"    Progress: {job['progress']*100:.1f}%")
                print(f"    Message: {job['message']}")
    except Exception as e:
        print(f"✗ Jobs endpoint failed: {e}")

    # Test 4: Check debug endpoint
    print("\n[TEST 4] Testing debug endpoint...")
    try:
        response = urllib.request.urlopen("http://localhost:8000/api/debug/jobs")
        data = json.loads(response.read().decode())
        print(f"✓ Debug endpoint working, {data['total']} jobs in memory")
    except Exception as e:
        print(f"✗ Debug endpoint failed: {e}")

    # Test 5: Instructions for manual test
    print("\n" + "=" * 70)
    print("MANUAL TEST INSTRUCTIONS")
    print("=" * 70)
    print("\nTo test if the backend is processing:")
    print("\n1. Make sure backend is running (you should see logs in terminal)")
    print("\n2. Open frontend in browser: http://localhost:5173")
    print("\n3. Upload both files (CBX and HC)")
    print("\n4. Click 'Start Matching'")
    print("\n5. Watch BACKEND TERMINAL for these logs (IN ORDER):")
    print("   ✓ 'CBX file saved: ...'")
    print("   ✓ 'HC file saved: ...'")
    print("   ✓ 'Scheduling background task...'")
    print("   ✓ '!!!! BACKGROUND TASK STARTED !!!!' ← CRITICAL")
    print("   ✓ 'Attempting to read CBX file...'")
    print("   ✓ 'CBX file read successfully...'")
    print("   ✓ 'Progress Update - Job: ...'")
    print("\n6. If you DON'T see '!!!! BACKGROUND TASK STARTED':")
    print("   - BackgroundTasks isn't working")
    print("   - Restart backend: Ctrl+C, then python3 main.py")
    print("\n7. Watch FRONTEND (bottom of page) 'Live Console' for:")
    print("   - [INFO] Poll: processing - X% - Matching...")
    print("\n8. Watch FRONTEND progress bar - should move 0% → 100%")
    print("\n" + "=" * 70)

    # Test 6: Check if any recent job is processing
    print("\n[TEST 6] Checking for active processing...")
    try:
        response = urllib.request.urlopen("http://localhost:8000/api/jobs")
        data = json.loads(response.read().decode())
        jobs = data.get('jobs', [])

        processing = [j for j in jobs if j['status'] in ('processing', 'pending')]
        if processing:
            print(f"✓ Found {len(processing)} active jobs")
            for job in processing:
                print(f"  - {job['job_id'][:8]}: {job['progress']*100:.1f}% - {job['message']}")
        else:
            print(f"  No active jobs currently processing")

        completed = [j for j in jobs if j['status'] == 'completed']
        failed = [j for j in jobs if j['status'] == 'failed']

        if completed:
            print(f"  ✓ {len(completed)} completed jobs")
        if failed:
            print(f"  ✗ {len(failed)} failed jobs")
            for job in failed[:2]:
                print(f"    - {job.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"✗ Error: {e}")

    print("\n" + "=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print("\nIf progress bar stays at 0%:")
    print("1. Check backend terminal for '!!!! BACKGROUND TASK STARTED' log")
    print("2. If missing, restart backend (Ctrl+C, then python3 main.py)")
    print("3. Make sure you restarted after code changes")
    print("4. Check browser console (F12) for JavaScript errors")
    print("5. Verify API_URL in frontend: http://localhost:8000")

    return True

if __name__ == "__main__":
    test_backend()

