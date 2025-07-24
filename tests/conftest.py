"""Pytest configuration and fixtures for LarkEditor Web tests."""

import asyncio
import pytest
import pytest_asyncio
import logging
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
import httpx

from app.main import app
from app.core.config import get_settings, setup_logging
from app.core.parser import get_parser
from app.core.state import get_session_manager


# Configure logging for tests
settings = get_settings()
settings.log_level = "WARNING"  # Reduce noise in tests
settings.log_to_file = False    # Don't write to file during tests
setup_logging(settings)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async client for testing async endpoints."""
    # Use the standard approach for testing FastAPI with async
    async with AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
def sample_grammars():
    """Sample grammars for testing."""
    return {
        "simple": """
start: expr
expr: NUMBER
%import common.NUMBER
%import common.WS
%ignore WS
        """.strip(),
        
        "arithmetic": """
start: expr
expr: term (("+" | "-") term)*
term: factor (("*" | "/") factor)*
factor: NUMBER | "(" expr ")"
%import common.NUMBER
%import common.WS
%ignore WS
        """.strip(),
        
        "invalid": """
start: expr
expr: INVALID_TOKEN
        """.strip(),
        
        "complex": """
start: statement+
statement: assignment | expression
assignment: IDENTIFIER "=" expression
expression: term (("+" | "-") term)*
term: factor (("*" | "/") factor)*
factor: NUMBER | IDENTIFIER | "(" expression ")"
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
%import common.NUMBER
%import common.WS
%ignore WS
        """.strip()
    }


@pytest.fixture
def sample_texts():
    """Sample texts for testing."""
    return {
        "simple_number": "42",
        "arithmetic": "3 + 4 * 2",
        "complex_arithmetic": "(1 + 2) * (3 - 4)",
        "assignment": "x = 10 + 5",
        "invalid": "invalid syntax here",
        "empty": "",
        "large": "1" * 1000  # Large input for stress testing
    }


@pytest.fixture
def sample_parse_settings():
    """Sample parse settings for testing."""
    from app.models.requests import ParseSettings, ParserType
    
    return {
        "default": ParseSettings(),
        "lalr": ParseSettings(parser=ParserType.LALR),
        "earley": ParseSettings(parser=ParserType.EARLEY),
        "debug": ParseSettings(debug=True),
        "custom_start": ParseSettings(start_rule="expression")
    }


@pytest_asyncio.fixture
async def parser_instance():
    """Get a parser instance for testing."""
    return get_parser()


@pytest_asyncio.fixture
async def session_manager():
    """Get a session manager instance for testing."""
    return get_session_manager()


@pytest.fixture
def websocket_messages():
    """Sample WebSocket messages for testing."""
    return {
        "grammar_change": {
            "type": "grammar_change",
            "session_id": "test_session_123",
            "data": {"content": "start: NUMBER\n%import common.NUMBER"}
        },
        "text_change": {
            "type": "text_change", 
            "session_id": "test_session_123",
            "data": {"content": "42"}
        },
        "force_parse": {
            "type": "force_parse",
            "session_id": "test_session_123",
            "data": {}
        },
        "settings_change": {
            "type": "settings_change",
            "session_id": "test_session_123",
            "data": {"parser": "lalr", "debug": True}
        }
    }


@pytest.fixture
def cleanup_sessions():
    """Cleanup sessions after tests."""
    yield
    # Clear all sessions after test but avoid creating event loop issues
    try:
        session_manager = get_session_manager()
        session_manager.sessions.clear()
        # Stop cleanup task to avoid event loop issues
        if session_manager.cleanup_task and not session_manager.cleanup_task.done():
            session_manager.cleanup_task.cancel()
    except RuntimeError:
        # Event loop not running, skip cleanup
        pass


@pytest.fixture
def cleanup_parser_cache():
    """Cleanup parser cache after tests."""
    yield
    # Clear parser cache after test
    parser = get_parser()
    parser.clear_cache()
    parser.active_parsers.clear()


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.sent_messages = []
        self.closed = False
        self.client = MockClient()
    
    async def send_json(self, data):
        """Mock send_json method."""
        self.sent_messages.append(data)
    
    async def close(self):
        """Mock close method."""
        self.closed = True


class MockClient:
    """Mock client for WebSocket testing."""
    
    def __init__(self):
        self.host = "127.0.0.1"


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    return MockWebSocket() 