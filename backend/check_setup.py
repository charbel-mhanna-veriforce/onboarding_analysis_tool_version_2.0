#!/usr/bin/env python3
"""
Simple diagnostic script - checks backend setup without external dependencies
"""
import os
import sys
from pathlib import Path

def check_backend_setup():
    print("=" * 60)
    print("Backend Setup Diagnostic")
    print("=" * 60)

    # Check 1: Working directory
    print("\n1. Current Directory:")
    cwd = os.getcwd()
    print(f"   {cwd}")

    # Check 2: main.py exists
    print("\n2. Checking main.py:")
    if os.path.exists('main.py'):
        print(f"   ✓ main.py found")
        # Check file size
        size = os.path.getsize('main.py')
        print(f"   ✓ Size: {size:,} bytes")
    else:
        print(f"   ✗ main.py NOT FOUND")
        print(f"   Run this script from the backend directory!")
        return False

    # Check 3: Required directories
    print("\n3. Checking directories:")
    for dir_name in ['uploads', 'outputs']:
        if os.path.exists(dir_name):
            print(f"   ✓ {dir_name}/ exists")
            # Count files
            files = os.listdir(dir_name)
            print(f"      ({len(files)} files)")
        else:
            print(f"   ✗ {dir_name}/ missing - creating...")
            os.makedirs(dir_name, exist_ok=True)
            print(f"   ✓ Created {dir_name}/")

    # Check 4: Python modules
    print("\n4. Checking Python modules:")
    modules = {
        'fastapi': 'FastAPI framework',
        'uvicorn': 'ASGI server',
        'pandas': 'Data processing',
        'rapidfuzz': 'Fuzzy matching',
        'openpyxl': 'Excel support'
    }

    missing = []
    for module, desc in modules.items():
        try:
            __import__(module)
            print(f"   ✓ {module:15} - {desc}")
        except ImportError:
            print(f"   ✗ {module:15} - MISSING!")
            missing.append(module)

    if missing:
        print(f"\n   Missing modules: {', '.join(missing)}")
        print(f"   Install with: pip install -r requirements.txt")
        return False

    # Check 5: Can import main module
    print("\n5. Testing main.py import:")
    try:
        sys.path.insert(0, '.')
        import main
        print(f"   ✓ main.py imports successfully")
        print(f"   ✓ FastAPI app object exists: {hasattr(main, 'app')}")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        print(f"\n   There may be syntax errors in main.py")
        return False

    # Check 6: Verify key functions exist
    print("\n6. Checking key components:")
    try:
        has_matcher = hasattr(main, 'ContractorMatcher')
        has_process = hasattr(main, 'process_matching_job')
        has_endpoint = hasattr(main, 'create_matching_job')

        print(f"   ✓ ContractorMatcher class: {has_matcher}")
        print(f"   ✓ process_matching_job function: {has_process}")
        print(f"   ✓ create_matching_job endpoint: {has_endpoint}")

        if not (has_matcher and has_process and has_endpoint):
            print(f"   ✗ Some components missing!")
            return False
    except Exception as e:
        print(f"   ✗ Error checking components: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ All checks passed!")
    print("=" * 60)
    print("\nYou can now start the backend:")
    print("  python3 main.py")
    print("\nOr with uvicorn directly:")
    print("  python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload")

    return True

if __name__ == "__main__":
    success = check_backend_setup()
    sys.exit(0 if success else 1)

