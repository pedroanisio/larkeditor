"""Application configuration settings."""

import logging
import sys
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Server settings
    host: str = "0.0.0.0"  # Bind to all interfaces
    port: int = 8000
    debug: bool = True
    
    # Logging settings
    log_level: str = "DEBUG"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "larkeditor.log"
    log_to_console: bool = True
    log_to_file: bool = True
    
    # Security settings
    max_upload_size: int = 50 * 1024 * 1024  # 50MB
    max_grammar_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = [".lark", ".txt", ".ebnf"]
    
    # Parsing settings
    max_parse_time: float = 30.0  # seconds
    max_grammar_complexity: int = 1000  # rules
    max_text_length: int = 1024 * 1024  # 1MB
    debounce_delay: float = 1.0  # seconds
    
    # Session settings
    session_timeout: int = 3600  # 1 hour
    max_sessions: int = 1000
    
    # Cache settings
    parse_cache_size: int = 100
    
    class Config:
        env_file = ".env"


def setup_logging(settings: Settings):
    """Setup application logging."""
    # Create formatters and handlers
    formatter = logging.Formatter(settings.log_format)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if settings.log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if settings.log_to_file:
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels to avoid noise
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    
    # Filter out noisy development server logs
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
    logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
    
    # Application loggers
    logging.getLogger("app").setLevel(getattr(logging, settings.log_level.upper()))
    logging.getLogger("lark").setLevel(logging.WARNING)  # Reduce lark verbosity


@lru_cache()
def get_settings():
    """Get cached settings instance."""
    return Settings()


def get_logger(name: str) -> logging.Logger:
    """Get logger with app prefix."""
    return logging.getLogger(f"app.{name}")