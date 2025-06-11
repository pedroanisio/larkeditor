# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LarkEditor is now a **web-based application** for creating and editing EBNF grammar files used by the Lark parsing library. It provides real-time AST generation and grammar validation through a modern web interface.

**Migration Status**: Successfully migrated from GTK3 desktop application to FastAPI + WebSocket web application.

### Original GTK Version
The `larkeditor/` directory contains the original GTK3-based desktop application (preserved for reference).

### New Web Version  
The `app/` directory contains the modern web-based implementation with FastAPI backend and Monaco Editor frontend.

## Development Commands

### Installation and Setup
```bash
# Install web application dependencies
pip install -r requirements.txt

# Or install original GTK version (requires GTK3, PyGObject, GtkSourceView)
pip install pygobject lark-parser
python3 setup.py develop
```

### Running the Web Application
```bash
# Development server with auto-reload
python run_dev.py

# Or using uvicorn directly
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Using Docker
docker-compose up --build
```

### Running the Original GTK Application
```bash
# Using the installed script (GTK version)
lark-editor [filename]

# Or running as module (GTK version)
python3 -m larkeditor [filename]
```

### Code Quality
```bash
# Lint code (follows flake8 with 120 char line limit)
flake8 app/ larkeditor/

# Type checking
mypy app/

# Format code
black app/
```

### API Documentation
```bash
# Access interactive API docs at:
# http://localhost:8000/api/docs (Swagger UI)
# http://localhost:8000/api/redoc (ReDoc)
```

## Architecture

### Web Application Architecture (app/)

#### Backend Components
- **FastAPI Application** (`app/main.py`) - ASGI web server with automatic API docs
- **Async Parser Service** (`app/core/parser.py`) - Thread-pool based async Lark parsing with caching
- **WebSocket Handler** (`app/websockets/parsing_ws.py`) - Real-time communication with 1-second debounce
- **Session Manager** (`app/core/state.py`) - Web session management with automatic cleanup
- **API Routes** (`app/api/`) - RESTful endpoints for parsing, files, and health checks
- **Pydantic Models** (`app/models/`) - Request/response validation and serialization

#### Frontend Components
- **Monaco Editor** - Professional code editor with Lark syntax highlighting
- **WebSocket Client** (`app/static/js/websocket-client.js`) - Real-time server communication
- **AST Renderer** (`app/static/js/ast-renderer.js`) - Interactive tree visualization
- **File Manager** (`app/static/js/file-manager.js`) - Upload/download with drag-and-drop
- **Editor Manager** (`app/static/js/editor-manager.js`) - Monaco editor integration

#### Key Patterns
- **Async/Await**: Non-blocking I/O throughout the backend
- **WebSocket Real-time**: Replaces GTK signals with web-compatible real-time updates
- **Session-based State**: Web-compatible state management with cleanup
- **RESTful API**: Standard HTTP endpoints for file operations and configuration
- **Component Architecture**: Modular JavaScript with ES6 modules

### Web UI Structure
```
Web Interface
├── Header (parser settings, file operations)
├── Main Content (3-panel layout)
│   ├── Grammar Editor (Monaco with Lark syntax)
│   ├── Text Editor (Monaco for test input)
│   └── Results Panel (AST tree or error display)
└── Status Bar (connection status, performance info)
```

### Web Data Flow
1. User edits grammar in Monaco Editor
2. JavaScript debounces changes (500ms) then sends via WebSocket
3. Server-side session manager updates state
4. Async parser validates and parses with thread-pool executor
5. Results broadcast to all WebSocket connections in session
6. Frontend updates AST visualization or error display
7. Monaco Editor highlights errors with decorations

### Original GTK Architecture (larkeditor/)
The original desktop application components are preserved in `larkeditor/` directory for reference.
Key differences from web version:
- **Synchronous**: GTK threading vs async/await
- **Desktop UI**: GTK widgets vs web technologies  
- **Local State**: In-memory vs session-based management
- **File System**: Direct access vs upload/download API

## Key Files

### Web Application (app/)
- `app/main.py` - FastAPI application entry point
- `app/core/parser.py` - Async Lark parser service with caching
- `app/core/state.py` - Session management and WebSocket handling
- `app/api/` - REST API endpoints (parsing, files, health)
- `app/websockets/` - WebSocket handlers for real-time communication
- `app/models/` - Pydantic request/response models
- `app/templates/index.html` - Main web interface
- `app/static/js/` - Frontend JavaScript modules
- `app/static/css/editor.css` - Web UI styling
- `requirements.txt` - Python dependencies for web version

### Original GTK Application (larkeditor/)
- `larkeditor/data/` - UI definitions (.ui), language specs (.lang), styles (.xml)
- `larkeditor/editor/` - Text editing components with syntax highlighting
- `larkeditor/utils/` - Utility classes (ObservableValue, error handling, file filters)

### Configuration & Deployment
- `run_dev.py` - Development server startup script
- `Dockerfile` - Container configuration for deployment
- `docker-compose.yml` - Multi-container orchestration

## Dependencies

### Web Version
- **fastapi** - Modern web framework with automatic API docs
- **uvicorn** - ASGI server for production deployment
- **pydantic** - Data validation and serialization
- **lark-parser** - Core parsing library (shared with GTK version)
- **websockets** - Real-time communication protocol
- **jinja2** - Template engine for HTML rendering

### Original GTK Version
- **lark-parser** - Core parsing library
- **PyGObject** - GTK3 Python bindings
- **GtkSourceView** - Syntax highlighting text widget

## Testing Notes

### Web Application Testing
When adding tests for the web version, consider:
- **API Testing**: Use pytest with FastAPI's TestClient for endpoint testing
- **WebSocket Testing**: Test real-time parsing with pytest-asyncio
- **Parser Testing**: Validate async parsing with various grammar samples
- **Session Management**: Test session cleanup and WebSocket connection handling
- **Frontend Testing**: Use Jest or similar for JavaScript module testing

### Original Application Testing
The GTK version currently has no automated tests. When adding tests:
- GTK widget testing with GtkTest
- Parser validation with sample grammars
- Threading behavior in BufferWatcher

## Migration Notes

The web version maintains feature parity with the GTK version while adding:
- **Cross-platform compatibility** - Runs in any modern web browser
- **Remote access** - Can be deployed on servers for team collaboration
- **Better performance** - Async/await architecture with connection pooling
- **Modern UI** - Monaco Editor with professional IDE features
- **API access** - Programmatic access to parsing functionality
- **Containerization** - Docker support for easy deployment

Files in `larkeditor/` directory are preserved for reference but the active development should focus on the `app/` directory for the web-based implementation.