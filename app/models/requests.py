"""Request models for the LarkEditor API."""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class ParserType(str, Enum):
    """Available parser types."""
    EARLEY = "earley"
    LALR = "lalr"
    CYK = "cyk"


class ParseSettings(BaseModel):
    """Parsing configuration settings."""
    parser: ParserType = ParserType.EARLEY
    start_rule: str = Field(default="start", min_length=1, max_length=100)
    debug: bool = False
    
    @validator('start_rule')
    def validate_start_rule(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Start rule must be alphanumeric with underscores and hyphens')
        return v


class ParseRequest(BaseModel):
    """Request to parse grammar with text input."""
    grammar: str = Field(..., min_length=1, max_length=10*1024*1024, description="Lark grammar definition")
    text: str = Field(..., max_length=1024*1024, description="Text to parse")
    settings: ParseSettings = ParseSettings()
    session_id: Optional[str] = Field(None, description="Session ID for state management")


class GrammarValidationRequest(BaseModel):
    """Request to validate grammar syntax."""
    grammar: str = Field(..., min_length=1, max_length=10*1024*1024)
    settings: ParseSettings = ParseSettings()


class FileUploadMetadata(BaseModel):
    """Metadata for file uploads."""
    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str
    size: int = Field(..., gt=0)
    
    @validator('filename')
    def validate_filename(cls, v):
        allowed_extensions = ['.lark', '.txt', '.ebnf']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'File must have one of these extensions: {allowed_extensions}')
        return v


class SessionRequest(BaseModel):
    """Request to create or manage a session."""
    session_id: Optional[str] = None
    initial_grammar: Optional[str] = None
    initial_text: Optional[str] = None
    settings: ParseSettings = ParseSettings()


class ExportRequest(BaseModel):
    """Request to export AST or results."""
    format: str = Field(..., pattern="^(json|xml|dot|png)$")
    session_id: str
    include_metadata: bool = False