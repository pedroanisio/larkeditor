#!/usr/bin/env python3
"""Simple server test to isolate startup issues."""

import sys
import traceback

def test_minimal_server():
    """Test a minimal FastAPI server."""
    print("🧪 Testing minimal FastAPI server...")
    
    try:
        from fastapi import FastAPI
        import uvicorn
        
        # Create minimal app
        app = FastAPI(title="Test Server")
        
        @app.get("/")
        def read_root():
            return {"message": "Server is working"}
        
        @app.get("/health")
        def health_check():
            return {"status": "ok"}
        
        print("✅ Minimal server created successfully")
        print("Starting server on http://0.0.0.0:8001...")
        print("Press Ctrl+C to stop")
        
        # Start server
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
        
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
    except Exception as e:
        print(f"❌ Minimal server failed: {e}")
        traceback.print_exc()

def test_main_server():
    """Test the main LarkEditor server."""
    print("🚀 Testing main LarkEditor server...")
    
    try:
        from app.main import app
        import uvicorn
        
        print("✅ Main app imported successfully")
        print("Starting LarkEditor server on http://0.0.0.0:8000...")
        print("Press Ctrl+C to stop")
        
        # Start main server
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug", reload=True)
        
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
    except Exception as e:
        print(f"❌ Main server failed: {e}")
        traceback.print_exc()
        
        print("\n🔍 Error Details:")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        
        # Additional debugging
        if "ModuleNotFoundError" in str(type(e)):
            print("\n💡 This looks like a missing dependency.")
            print("Try: pip install -r requirements.txt")
        elif "ImportError" in str(type(e)):
            print("\n💡 This looks like an import issue.")
            print("Check file paths and module structure")
        elif "ValidationError" in str(type(e)):
            print("\n💡 This looks like a configuration issue.")
            print("Check app/core/config.py")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "minimal":
        test_minimal_server()
    else:
        print("🔧 LarkEditor Server Test")
        print("=" * 30)
        print("Choose test mode:")
        print("1. Main server (default)")
        print("2. Minimal server (for debugging)")
        print()
        
        choice = input("Enter choice (1 or 2, default=1): ").strip()
        
        if choice == "2":
            test_minimal_server()
        else:
            test_main_server()