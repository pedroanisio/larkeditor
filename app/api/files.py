"""API routes for file operations."""

import os
import tempfile
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Response
from fastapi.responses import FileResponse

from ..models.requests import FileUploadMetadata, ExportRequest
from ..models.responses import FileInfo, ExportResult
from ..core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/upload", response_model=FileInfo)
async def upload_file(
    file: UploadFile = File(...),
    file_type: Optional[str] = "grammar"
) -> FileInfo:
    """Upload a grammar or text file."""
    
    # Validate file size
    if file.size and file.size > settings.max_upload_size:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Validate file extension
    if not any(file.filename.lower().endswith(ext) for ext in settings.allowed_extensions):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {settings.allowed_extensions}"
        )
    
    try:
        # Read file content
        content = await file.read()
        
        # Basic content validation
        if b'\x00' in content:
            raise HTTPException(status_code=400, detail="Binary files not supported")
        
        # Validate content size
        if len(content) > settings.max_grammar_size:
            raise HTTPException(status_code=413, detail="File content too large")
        
        # Store file temporarily (in a real app, you'd use proper storage)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        temp_file.write(content)
        temp_file.close()
        
        file_info = FileInfo(
            filename=file.filename,
            size=len(content),
            content_type=file.content_type or "text/plain",
            upload_time=datetime.now()
        )
        
        return file_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/download/{filename}")
async def download_file(filename: str) -> FileResponse:
    """Download a previously uploaded file."""
    # In a real app, you'd track uploaded files properly
    # This is a simplified implementation
    
    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = os.path.join(tempfile.gettempdir(), filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.post("/export", response_model=ExportResult)
async def export_results(request: ExportRequest) -> ExportResult:
    """Export parsing results in various formats."""
    # This would integrate with the session management system
    # For now, return a placeholder
    
    if request.format not in ["json", "xml", "dot", "png"]:
        raise HTTPException(status_code=400, detail="Unsupported export format")
    
    # Placeholder implementation
    content = f"Export in {request.format} format - not yet implemented"
    
    return ExportResult(
        format=request.format,
        content=content,
        filename=f"export.{request.format}",
        content_type=f"application/{request.format}",
        size=len(content)
    )