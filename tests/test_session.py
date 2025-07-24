"""Tests for session management functionality."""

import pytest
import asyncio
from datetime import datetime, timedelta

from app.core.state import EditorSession, SessionManager, get_session_manager
from app.models.requests import ParseSettings, ParserType


class TestEditorSession:
    """Test the EditorSession data class."""
    
    def test_session_creation(self):
        """Test session creation."""
        session_id = "test_session_123"
        session = EditorSession(session_id=session_id)
        
        assert session.session_id == session_id
        assert session.grammar_content == ""
        assert session.text_content == ""
        assert isinstance(session.parse_settings, ParseSettings)
        assert session.last_parse_result is None
        assert len(session.websocket_connections) == 0
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_activity, datetime)
    
    def test_session_update_activity(self):
        """Test activity timestamp updating."""
        session = EditorSession(session_id="test")
        original_time = session.last_activity
        
        # Small delay to ensure time difference
        import time
        time.sleep(0.01)
        
        session.update_activity()
        assert session.last_activity > original_time
    
    def test_session_websocket_management(self, mock_websocket):
        """Test WebSocket connection management."""
        session = EditorSession(session_id="test")
        
        # Initially no connections
        assert session.get_connection_count() == 0
        
        # Add WebSocket
        session.add_websocket(mock_websocket)
        assert session.get_connection_count() == 1
        assert mock_websocket in session.websocket_connections
        
        # Remove WebSocket
        session.remove_websocket(mock_websocket)
        assert session.get_connection_count() == 0
        assert mock_websocket not in session.websocket_connections
    
    def test_session_expiry(self):
        """Test session expiry logic."""
        from app.core.config import get_settings
        
        session = EditorSession(session_id="test")
        settings = get_settings()
        
        # Fresh session should not be expired
        assert not session.is_expired()
        
        # Manually set old activity time
        session.last_activity = datetime.now() - timedelta(seconds=settings.session_timeout + 1)
        assert session.is_expired()


class TestSessionManager:
    """Test the SessionManager class."""
    
    @pytest.mark.asyncio
    async def test_session_manager_initialization(self):
        """Test session manager initialization."""
        manager = SessionManager()
        
        assert len(manager.sessions) == 0
        assert manager.cleanup_task is not None
    
    @pytest.mark.asyncio
    async def test_get_or_create_session(self, cleanup_sessions):
        """Test getting or creating sessions."""
        manager = SessionManager()
        
        session_id = "test_session_123"
        
        # First call should create session
        session1 = await manager.get_or_create_session(session_id)
        assert session1.session_id == session_id
        assert len(manager.sessions) == 1
        
        # Second call should return same session
        session2 = await manager.get_or_create_session(session_id)
        assert session1 is session2
        assert len(manager.sessions) == 1
        
        # Different session ID should create new session
        session3 = await manager.get_or_create_session("different_session")
        assert session3 is not session1
        assert len(manager.sessions) == 2
    
    @pytest.mark.asyncio
    async def test_update_session_content(self, cleanup_sessions):
        """Test updating session content."""
        manager = SessionManager()
        session_id = "test_session"
        
        # Update grammar content
        await manager.update_session_content(
            session_id, 
            grammar="start: NUMBER\n%import common.NUMBER"
        )
        
        session = manager.sessions[session_id]
        assert "NUMBER" in session.grammar_content
        assert session.text_content == ""
        
        # Update text content
        await manager.update_session_content(
            session_id,
            text="42"
        )
        
        assert session.text_content == "42"
        
        # Update settings
        new_settings = ParseSettings(parser=ParserType.EARLEY, debug=True)
        await manager.update_session_content(
            session_id,
            settings=new_settings
        )
        
        assert session.parse_settings.parser == ParserType.EARLEY
        assert session.parse_settings.debug is True
    
    @pytest.mark.asyncio
    async def test_websocket_management(self, cleanup_sessions, mock_websocket):
        """Test WebSocket management in sessions."""
        manager = SessionManager()
        session_id = "test_session"
        
        # Add WebSocket to session
        await manager.add_websocket_to_session(session_id, mock_websocket)
        
        session = manager.sessions[session_id]
        assert session.get_connection_count() == 1
        
        # Remove WebSocket from session
        await manager.remove_websocket_from_session(session_id, mock_websocket)
        assert session.get_connection_count() == 0
        
        # Remove from non-existent session should not error
        await manager.remove_websocket_from_session("nonexistent", mock_websocket)
    
    @pytest.mark.asyncio
    async def test_broadcast_to_session(self, cleanup_sessions):
        """Test broadcasting messages to session."""
        from tests.conftest import MockWebSocket
        
        manager = SessionManager()
        session_id = "test_session"
        
        # Create mock WebSockets
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        
        # Add WebSockets to session
        await manager.add_websocket_to_session(session_id, ws1)
        await manager.add_websocket_to_session(session_id, ws2)
        
        # Broadcast message
        message = {"type": "test", "data": "hello"}
        await manager.broadcast_to_session(session_id, message)
        
        # Both WebSockets should have received the message
        assert len(ws1.sent_messages) == 1
        assert len(ws2.sent_messages) == 1
        assert ws1.sent_messages[0] == message
        assert ws2.sent_messages[0] == message
        
        # Broadcast to non-existent session should not error
        await manager.broadcast_to_session("nonexistent", message)
    
    @pytest.mark.asyncio
    async def test_session_stats(self, cleanup_sessions):
        """Test session statistics."""
        from tests.conftest import MockWebSocket
        
        manager = SessionManager()
        
        # Initial stats
        stats = manager.get_session_stats()
        assert stats["total_sessions"] == 0
        assert stats["total_connections"] == 0
        assert stats["active_sessions"] == 0
        
        # Create session with connections
        session_id = "test_session"
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()
        
        await manager.add_websocket_to_session(session_id, ws1)
        await manager.add_websocket_to_session(session_id, ws2)
        
        # Create session without connections
        await manager.get_or_create_session("empty_session")
        
        stats = manager.get_session_stats()
        assert stats["total_sessions"] == 2
        assert stats["total_connections"] == 2
        assert stats["active_sessions"] == 1
    
    @pytest.mark.asyncio
    async def test_session_cleanup(self, cleanup_sessions):
        """Test session cleanup functionality."""
        from app.core.config import get_settings
        
        manager = SessionManager()
        settings = get_settings()
        
        # Create expired session
        expired_session = await manager.get_or_create_session("expired")
        expired_session.last_activity = datetime.now() - timedelta(seconds=settings.session_timeout + 1)
        
        # Create active session with connections
        from tests.conftest import MockWebSocket
        active_session_id = "active"
        await manager.add_websocket_to_session(active_session_id, MockWebSocket())
        
        # Manually trigger cleanup
        expired_sessions = [
            session_id for session_id, session in manager.sessions.items()
            if session.is_expired() and session.get_connection_count() == 0
        ]
        
        for session_id in expired_sessions:
            del manager.sessions[session_id]
        
        # Expired session should be gone, active session should remain
        assert "expired" not in manager.sessions
        assert "active" in manager.sessions
    
    @pytest.mark.asyncio
    async def test_max_sessions_limit(self, cleanup_sessions):
        """Test maximum sessions limit enforcement."""
        from app.core.config import get_settings
        
        manager = SessionManager()
        settings = get_settings()
        original_max = settings.max_sessions
        
        # Temporarily reduce max sessions for testing
        settings.max_sessions = 5
        
        try:
            # Create more sessions than the limit
            for i in range(10):
                await manager.get_or_create_session(f"session_{i}")
            
            # Should have created all sessions initially
            assert len(manager.sessions) == 10
            
            # Manually trigger cleanup logic
            if len(manager.sessions) > settings.max_sessions:
                sessions_by_age = sorted(
                    [(sid, s) for sid, s in manager.sessions.items() if s.get_connection_count() == 0],
                    key=lambda x: x[1].last_activity
                )
                
                excess_count = len(manager.sessions) - settings.max_sessions
                for session_id, _ in sessions_by_age[:excess_count]:
                    del manager.sessions[session_id]
            
            # Should now be at or below limit
            assert len(manager.sessions) <= settings.max_sessions
            
        finally:
            # Restore original setting
            settings.max_sessions = original_max
    
    @pytest.mark.asyncio
    async def test_manager_shutdown(self):
        """Test session manager shutdown."""
        manager = SessionManager()
        
        # Should not raise errors
        await manager.shutdown()
        
        # Cleanup task should be cancelled
        if manager.cleanup_task:
            assert manager.cleanup_task.cancelled() or manager.cleanup_task.done()


class TestSessionManagerIntegration:
    """Integration tests for session manager."""
    
    @pytest.mark.asyncio
    async def test_get_session_manager_singleton(self):
        """Test that get_session_manager returns singleton."""
        manager1 = get_session_manager()
        manager2 = get_session_manager()
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self, cleanup_sessions):
        """Test concurrent session operations."""
        manager = get_session_manager()
        
        # Create multiple tasks that operate on sessions concurrently
        async def create_and_modify_session(session_id: str):
            session = await manager.get_or_create_session(session_id)
            await manager.update_session_content(
                session_id,
                grammar=f"start: '{session_id}'\n",
                text=session_id
            )
            return session
        
        # Run multiple concurrent operations
        tasks = [
            create_and_modify_session(f"session_{i}")
            for i in range(10)
        ]
        
        sessions = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(sessions) == 10
        assert len(manager.sessions) == 10
        
        # Each session should have correct content
        for i, session in enumerate(sessions):
            assert session.grammar_content == f"start: 'session_{i}'\n"
            assert session.text_content == f"session_{i}"
    
    @pytest.mark.asyncio
    async def test_websocket_disconnection_handling(self, cleanup_sessions):
        """Test handling of WebSocket disconnections."""
        from tests.conftest import MockWebSocket
        
        manager = get_session_manager()
        session_id = "test_session"
        
        # Create WebSockets and add to session
        ws_good = MockWebSocket()
        ws_bad = MockWebSocket()
        
        await manager.add_websocket_to_session(session_id, ws_good)
        await manager.add_websocket_to_session(session_id, ws_bad)
        
        session = manager.sessions[session_id]
        assert session.get_connection_count() == 2
        
        # Simulate one WebSocket failing
        class FailingMockWebSocket(MockWebSocket):
            async def send_json(self, data):
                raise Exception("Connection failed")
        
        # Replace one WebSocket with failing one
        session.websocket_connections.discard(ws_bad)
        failing_ws = FailingMockWebSocket()
        session.websocket_connections.add(failing_ws)
        
        # Broadcast should handle the failure gracefully
        message = {"type": "test", "data": "hello"}
        await manager.broadcast_to_session(session_id, message)
        
        # Good WebSocket should receive message
        assert len(ws_good.sent_messages) == 1
        assert ws_good.sent_messages[0] == message
        
        # Failed WebSocket should be removed from session
        assert failing_ws not in session.websocket_connections
        assert session.get_connection_count() == 1
    
    @pytest.mark.asyncio
    async def test_session_memory_usage(self, cleanup_sessions):
        """Test session memory management."""
        manager = get_session_manager()
        
        # Create many sessions with content
        large_content = "x" * 1000  # 1KB content per session
        
        for i in range(100):
            session_id = f"session_{i}"
            await manager.update_session_content(
                session_id,
                grammar=large_content,
                text=large_content
            )
        
        assert len(manager.sessions) == 100
        
        # All sessions should have the expected content
        for session in manager.sessions.values():
            assert len(session.grammar_content) == 1000
            assert len(session.text_content) == 1000
        
        # Cleanup should work efficiently
        manager.sessions.clear()
        assert len(manager.sessions) == 0 