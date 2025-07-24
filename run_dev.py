#!/usr/bin/env python3
"""Development server startup script for LarkEditor Web."""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🚀 Starting LarkEditor Web Development Server...")
    print("📡 Server will be available at: http://0.0.0.0:8000")
    print("📚 API documentation at: http://0.0.0.0:8000/api/docs") 
    print("🛑 Press Ctrl+C to stop the server")
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",  # Changed from debug to reduce noise
        access_log=True
    )