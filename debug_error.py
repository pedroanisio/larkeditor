#!/usr/bin/env python3
"""Debug script to identify unknown errors in LarkEditor Web."""

import sys
import traceback
import asyncio
from pathlib import Path

def check_imports():
    """Check if all required imports work."""
    print("🔍 Checking Python imports...")
    
    try:
        import fastapi
        print(f"✅ FastAPI {fastapi.__version__}")
    except Exception as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print(f"✅ Uvicorn {uvicorn.__version__}")
    except Exception as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import lark
        print(f"✅ Lark {lark.__version__}")
    except Exception as e:
        print(f"❌ Lark import failed: {e}")
        return False
    
    try:
        import pydantic
        print(f"✅ Pydantic {pydantic.__version__}")
    except Exception as e:
        print(f"❌ Pydantic import failed: {e}")
        return False
    
    try:
        from pydantic_settings import BaseSettings
        print("✅ Pydantic Settings")
    except Exception as e:
        print(f"❌ Pydantic Settings import failed: {e}")
        return False
    
    return True

def check_file_structure():
    """Check if all required files exist."""
    print("\n📁 Checking file structure...")
    
    required_files = [
        "app/main.py",
        "app/__init__.py",
        "app/core/config.py",
        "app/core/parser.py",
        "app/models/requests.py",
        "app/models/responses.py",
        "app/api/parsing.py",
        "app/websockets/parsing_ws.py",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def test_app_import():
    """Test importing the main app."""
    print("\n🚀 Testing app import...")
    
    try:
        from app.main import app
        print("✅ Main app imported successfully")
        return True
    except Exception as e:
        print(f"❌ App import failed: {e}")
        traceback.print_exc()
        return False

def test_config():
    """Test configuration loading."""
    print("\n⚙️ Testing configuration...")
    
    try:
        from app.core.config import get_settings
        settings = get_settings()
        print(f"✅ Config loaded: host={settings.host}, port={settings.port}")
        return True
    except Exception as e:
        print(f"❌ Config failed: {e}")
        traceback.print_exc()
        return False

def test_parser():
    """Test parser initialization."""
    print("\n🔍 Testing parser...")
    
    try:
        from app.core.parser import get_parser
        parser = get_parser()
        print("✅ Parser initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Parser failed: {e}")
        traceback.print_exc()
        return False

async def test_simple_parse():
    """Test a simple parse operation."""
    print("\n⚡ Testing simple parse...")
    
    try:
        from app.core.parser import get_parser
        from app.models.requests import ParseSettings
        
        parser = get_parser()
        settings = ParseSettings()
        
        # Simple grammar
        grammar = "start: NUMBER\\n%import common.NUMBER\\n%import common.WS\\n%ignore WS"
        text = "42"
        
        result = await parser.parse_async(grammar, text, settings)
        print(f"✅ Parse result: {result.status}")
        return True
    except Exception as e:
        print(f"❌ Parse failed: {e}")
        traceback.print_exc()
        return False

def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Python version compatible")
        return True
    else:
        print("❌ Python version too old (need 3.8+)")
        return False

def check_working_directory():
    """Check current working directory."""
    print("\n📂 Checking working directory...")
    
    cwd = Path.cwd()
    print(f"Current directory: {cwd}")
    
    # Check if we're in the right directory
    if (cwd / "app").exists() and (cwd / "app" / "main.py").exists():
        print("✅ Working directory is correct")
        return True
    else:
        print("❌ Wrong working directory - should be in larkeditor root")
        print("Run: cd /home/pals/code/grammar/larkeditor")
        return False

def run_startup_test():
    """Test the actual startup process."""
    print("\n🚀 Testing startup process...")
    
    try:
        # Import main components
        from app.main import app
        from app.core.config import get_settings
        
        settings = get_settings()
        
        # Try to create the app
        print(f"App title: {app.title}")
        print(f"App version: {app.version}")
        print("✅ App startup test passed")
        return True
        
    except Exception as e:
        print(f"❌ Startup test failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run all diagnostic tests."""
    print("🔧 LarkEditor Web Error Diagnostic Tool")
    print("=" * 50)
    
    # Store test results
    tests = []
    
    # Run tests
    tests.append(("Python Version", check_python_version()))
    tests.append(("Working Directory", check_working_directory()))
    tests.append(("File Structure", check_file_structure()))
    tests.append(("Python Imports", check_imports()))
    tests.append(("Configuration", test_config()))
    tests.append(("App Import", test_app_import()))
    tests.append(("Parser Init", test_parser()))
    tests.append(("Simple Parse", await test_simple_parse()))
    tests.append(("Startup Test", run_startup_test()))
    
    # Summary
    print("\n📊 Test Results Summary:")
    passed = 0
    for test_name, result in tests:
        status = "PASS" if result else "FAIL"
        icon = "✅" if result else "❌"
        print(f"{icon} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! The error might be:")
        print("   1. Network/firewall issue")
        print("   2. Port already in use")
        print("   3. Permission issue")
        print("   4. Browser-specific problem")
        print("\nTry:")
        print("   python run_dev.py")
        print("   or")
        print("   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    else:
        print("\n❌ Some tests failed. Fix the issues above and try again.")
    
    return passed == len(tests)

if __name__ == "__main__":
    asyncio.run(main())