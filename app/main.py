"""FastAPI application entry point for LarkEditor web version."""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .api import parsing, files, health
from .websockets import parsing_ws
from .core.config import get_settings, setup_logging, get_logger

# Initialize settings and logging
settings = get_settings()
setup_logging(settings)
logger = get_logger("main")

logger.info("Starting LarkEditor Web application...")
logger.debug(f"Settings: host={settings.host}, port={settings.port}, debug={settings.debug}")

app = FastAPI(
    title="LarkEditor Web",
    description="Web-based EBNF grammar editor for Lark parsing library",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware for WebSocket and API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, be more specific
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
logger.info("Mounting static files...")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
logger.info("Setting up templates...")
templates = Jinja2Templates(directory="app/templates")

# Include routers
logger.info("Including API routers...")
app.include_router(parsing.router, prefix="/api", tags=["parsing"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(parsing_ws.router, prefix="/ws", tags=["websockets"])


@app.get("/")
async def root(request: Request):
    """Serve the main editor interface."""
    logger.debug("Serving main editor interface")
    return templates.TemplateResponse("index.html", {"request": request})


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("LarkEditor Web application started successfully")
    logger.info(f"Available at: http://{settings.host}:{settings.port}")
    logger.info(f"API docs at: http://{settings.host}:{settings.port}/api/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down LarkEditor Web application...")
    # Cleanup session manager
    from .core.state import get_session_manager
    session_manager = get_session_manager()
    await session_manager.shutdown()
    logger.info("Application shutdown complete")


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting application with uvicorn...")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )