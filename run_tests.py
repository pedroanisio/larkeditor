#!/usr/bin/env python3
"""
Test runner script for LarkEditor Web application.

This script runs the comprehensive test suite and provides detailed reporting.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        elapsed = time.time() - start_time
        
        print(f"Exit code: {result.returncode}")
        print(f"Execution time: {elapsed:.2f} seconds")
        
        if result.stdout:
            print(f"\nSTDOUT:\n{result.stdout}")
        
        if result.stderr:
            print(f"\nSTDERR:\n{result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"Command timed out after 300 seconds")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Run the comprehensive test suite."""
    print("LarkEditor Web - Comprehensive Test Suite")
    print("=========================================")
    
    # Check if we're in the right directory
    if not Path("app").exists() or not Path("tests").exists():
        print("Error: Must be run from project root directory")
        sys.exit(1)
    
    # Test commands to run
    test_commands = [
        # 1. Basic syntax check
        ("python -m py_compile app/main.py", "Python syntax check"),
        
        # 2. Import check
        ("python -c 'import app.main; print(\"Imports successful\")'", "Import validation"),
        
        # 3. Parser tests
        ("python -m pytest tests/test_parser.py -v", "Parser functionality tests"),
        
        # 4. API tests
        ("python -m pytest tests/test_api.py -v", "API endpoint tests"),
        
        # 5. Session management tests
        ("python -m pytest tests/test_session.py -v", "Session management tests"),
        
        # 6. Full test suite
        ("python -m pytest tests/ -v --tb=short", "Complete test suite"),
        
        # 7. Test coverage (if coverage installed)
        ("python -m pytest tests/ --cov=app --cov-report=term-missing", "Test coverage analysis"),
    ]
    
    results = []
    
    for command, description in test_commands:
        success = run_command(command, description)
        results.append((description, success))
        
        if not success and "coverage" not in command.lower():
            print(f"\n❌ FAILED: {description}")
            print("Continuing with remaining tests...")
        else:
            print(f"\n✅ PASSED: {description}")
    
    # Summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:12} {description}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 