"""Health check and system status endpoints."""

import time
from datetime import datetime
from fastapi import APIRouter

from ..models.responses import HealthStatus
from ..core.parser import get_parser

router = APIRouter()

# Track app start time
_start_time = time.time()


@router.get("/health", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """Get application health status."""
    parser = get_parser()
    stats = parser.get_stats()
    
    return HealthStatus(
        status="healthy",
        version="2.0.0",
        uptime=time.time() - _start_time,
        active_sessions=0,  # Will be populated when session management is implemented
        total_parses=stats["parse_count"],
        cache_size=stats["cache_size"]
    )


@router.get("/version")
async def get_version() -> dict:
    """Get application version information."""
    return {
        "version": "2.0.0",
        "api_version": "v1",
        "build_time": datetime.now().isoformat()
    }