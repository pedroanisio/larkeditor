"""Response models for the LarkEditor API."""

from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ParseStatus(str, Enum):
    """Status of parsing operation."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    INVALID_GRAMMAR = "invalid_grammar"
    INVALID_TEXT = "invalid_text"


class ErrorType(str, Enum):
    """Types of parsing errors."""
    GRAMMAR_ERROR = "grammar_error"
    PARSE_ERROR = "parse_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    INTERNAL_ERROR = "internal_error"


class ParseError(BaseModel):
    """Detailed error information."""
    type: ErrorType
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    context: Optional[str] = None
    suggestions: Optional[List[str]] = None


class ASTNode(BaseModel):
    """AST tree node representation."""
    type: str
    data: str
    children: List[Union['ASTNode', str]] = []
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    line: Optional[int] = None
    column: Optional[int] = None


# Enable forward references for recursive model
ASTNode.model_rebuild()


class ParseResult(BaseModel):
    """Result of parsing operation."""
    status: ParseStatus
    tree: Optional[ASTNode] = None
    error: Optional[ParseError] = None
    parse_time: float = Field(..., description="Parse time in seconds")
    grammar_hash: str = Field(..., description="Hash of grammar for caching")
    timestamp: datetime = Field(default_factory=datetime.now)


class GrammarValidationResult(BaseModel):
    """Result of grammar validation."""
    is_valid: bool
    errors: List[ParseError] = []
    warnings: List[str] = []
    rule_count: int
    terminal_count: int


class SessionInfo(BaseModel):
    """Information about editing session."""
    session_id: str
    created_at: datetime
    last_activity: datetime
    grammar_content: str = ""
    text_content: str = ""
    settings: Dict[str, Any] = {}
    connection_count: int = 0


class FileInfo(BaseModel):
    """Information about uploaded/downloaded files."""
    filename: str
    size: int
    content_type: str
    upload_time: datetime
    session_id: Optional[str] = None


class HealthStatus(BaseModel):
    """Application health status."""
    status: str = "healthy"
    version: str
    uptime: float
    active_sessions: int
    total_parses: int
    cache_size: int


class ExportResult(BaseModel):
    """Result of export operation."""
    format: str
    content: Union[str, bytes]
    filename: str
    content_type: str
    size: int


class WebSocketMessage(BaseModel):
    """WebSocket message structure."""
    type: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any]