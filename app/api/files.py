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
    from ..core.state import get_session_manager
    
    if request.format not in ["json", "xml", "dot", "text"]:
        raise HTTPException(status_code=400, detail="Unsupported export format")
    
    # Get session and parse result
    session_manager = get_session_manager()
    if request.session_id not in session_manager.sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = session_manager.sessions[request.session_id]
    if not session.last_parse_result or not session.last_parse_result.tree:
        raise HTTPException(status_code=400, detail="No parse results to export")
    
    result = session.last_parse_result
    
    try:
        if request.format == "json":
            content = result.tree.json() if hasattr(result.tree, 'json') else str(result.tree)
            content_type = "application/json"
        elif request.format == "xml":
            # Convert AST to XML format
            content = f'<?xml version="1.0" encoding="UTF-8"?>\\n<ast>\\n{_ast_to_xml(result.tree, 1)}\\n</ast>'
            content_type = "application/xml"
        elif request.format == "dot":
            # Convert AST to Graphviz DOT format
            content = _ast_to_dot(result.tree)
            content_type = "text/vnd.graphviz"
        elif request.format == "text":
            # Convert AST to plain text
            content = _ast_to_text(result.tree, 0)
            content_type = "text/plain"
        
        if request.include_metadata:
            metadata = {
                "export_time": datetime.now().isoformat(),
                "session_id": request.session_id,
                "parse_time": result.parse_time,
                "grammar_hash": result.grammar_hash,
                "parser_status": result.status
            }
            
            if request.format == "json":
                import json
                data = json.loads(content) if content.startswith('{') else {"tree": content}
                data["metadata"] = metadata
                content = json.dumps(data, indent=2)
        
        return ExportResult(
            format=request.format,
            content=content,
            filename=f"parse_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.format}",
            content_type=content_type,
            size=len(content)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


def _ast_to_xml(node, depth=0):
    """Convert AST node to XML format."""
    indent = "  " * depth
    if hasattr(node, 'type') and node.type == 'tree':
        xml = f'{indent}<tree data="{_escape_xml(node.data)}">'
        if hasattr(node, 'children'):
            for child in node.children:
                xml += f'\\n{_ast_to_xml(child, depth + 1)}'
        xml += f'\\n{indent}</tree>'
        return xml
    else:
        data = getattr(node, 'data', str(node))
        return f'{indent}<token data="{_escape_xml(data)}" />'


def _ast_to_dot(node):
    """Convert AST node to Graphviz DOT format."""
    dot = 'digraph AST {\\n'
    counter = [0]  # Use list for mutable counter
    
    def _add_node(n, node_id):
        if hasattr(n, 'type') and n.type == 'tree':
            dot_content = f'  {node_id} [label="{_escape_dot(n.data)}" shape=ellipse];\\n'
            if hasattr(n, 'children'):
                for child in n.children:
                    counter[0] += 1
                    child_id = counter[0]
                    dot_content += f'  {node_id} -> {child_id};\\n'
                    dot_content += _add_node(child, child_id)
            return dot_content
        else:
            data = getattr(n, 'data', str(n))
            return f'  {node_id} [label="{_escape_dot(data)}" shape=box];\\n'
    
    dot += _add_node(node, 0)
    dot += '}\\n'
    return dot


def _ast_to_text(node, depth=0):
    """Convert AST node to plain text format."""
    indent = "  " * depth
    if hasattr(node, 'type') and node.type == 'tree':
        text = f'{indent}{node.data}\\n'
        if hasattr(node, 'children'):
            for child in node.children:
                text += _ast_to_text(child, depth + 1)
        return text
    else:
        data = getattr(node, 'data', str(node))
        return f'{indent}"{data}"\\n'


def _escape_xml(text):
    """Escape XML special characters."""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _escape_dot(text):
    """Escape DOT special characters."""
    return str(text).replace('\\\\', '\\\\\\\\').replace('"', '\\\\"').replace('\\n', '\\\\n')