"""Session and state management for web-based editor."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, List
from dataclasses import dataclass, field

from fastapi import WebSocket

from ..models.requests import ParseSettings
from ..models.responses import ParseResult
from .config import get_settings, get_logger

settings = get_settings()
logger = get_logger("state")


@dataclass
class EditorSession:
    """Editor session state."""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    grammar_content: str = ""
    text_content: str = ""
    parse_settings: ParseSettings = field(default_factory=ParseSettings)
    last_parse_result: Optional[ParseResult] = None
    tree_expand_state: List[List[int]] = field(default_factory=list)
    websocket_connections: Set[WebSocket] = field(default_factory=set)
    
    def __post_init__(self):
        logger.debug(f"Created session {self.session_id[:8]}...")
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()
        logger.debug(f"Updated activity for session {self.session_id[:8]}...")
    
    def add_websocket(self, websocket: WebSocket):
        """Add WebSocket connection to session."""
        self.websocket_connections.add(websocket)
        self.update_activity()
        logger.debug(f"Added WebSocket to session {self.session_id[:8]}... (total: {len(self.websocket_connections)})")
    
    def remove_websocket(self, websocket: WebSocket):
        """Remove WebSocket connection from session."""
        self.websocket_connections.discard(websocket)
        self.update_activity()
        logger.debug(f"Removed WebSocket from session {self.session_id[:8]}... (total: {len(self.websocket_connections)})")
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        expiry_time = self.last_activity + timedelta(seconds=settings.session_timeout)
        expired = datetime.now() > expiry_time
        if expired:
            logger.debug(f"Session {self.session_id[:8]}... has expired")
        return expired
    
    def get_connection_count(self) -> int:
        """Get number of active WebSocket connections."""
        return len(self.websocket_connections)


class SessionManager:
    """Manages editor sessions and WebSocket connections."""
    
    def __init__(self):
        self.sessions: Dict[str, EditorSession] = {}
        self.cleanup_task: Optional[asyncio.Task] = None
        logger.info("Initialized SessionManager")
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start the session cleanup background task."""
        try:
            if self.cleanup_task is None or self.cleanup_task.done():
                self.cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
                logger.info("Started session cleanup background task")
        except RuntimeError:
            # No event loop running (likely in tests), skip background task
            logger.debug("No event loop available, skipping cleanup task")
            self.cleanup_task = None
    
    async def _cleanup_expired_sessions(self):
        """Background task to clean up expired sessions."""
        logger.info("Session cleanup task started")
        cleanup_count = 0
        
        while True:
            try:
                expired_sessions = [
                    session_id for session_id, session in self.sessions.items()
                    if session.is_expired() and session.get_connection_count() == 0
                ]
                
                for session_id in expired_sessions:
                    del self.sessions[session_id]
                    cleanup_count += 1
                    logger.debug(f"Cleaned up expired session {session_id[:8]}...")
                
                # Also enforce max sessions limit
                excess_count = 0
                if len(self.sessions) > settings.max_sessions:
                    # Remove oldest sessions without connections
                    sessions_by_age = sorted(
                        [(sid, s) for sid, s in self.sessions.items() if s.get_connection_count() == 0],
                        key=lambda x: x[1].last_activity
                    )
                    
                    excess_count = len(self.sessions) - settings.max_sessions
                    for session_id, _ in sessions_by_age[:excess_count]:
                        del self.sessions[session_id]
                        cleanup_count += 1
                        logger.debug(f"Cleaned up excess session {session_id[:8]}...")
                
                if len(expired_sessions) > 0 or excess_count > 0:
                    logger.info(f"Session cleanup: {len(expired_sessions)} expired, {excess_count} excess (total cleaned: {cleanup_count})")
                
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
            except Exception as e:
                logger.error(f"Session cleanup error: {str(e)}")
                await asyncio.sleep(60)  # Retry after 1 minute on error
    
    async def get_or_create_session(self, session_id: str) -> EditorSession:
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            logger.info(f"Creating new session {session_id[:8]}...")
            self.sessions[session_id] = EditorSession(session_id=session_id)
        else:
            logger.debug(f"Retrieved existing session {session_id[:8]}...")
        
        session = self.sessions[session_id]
        session.update_activity()
        return session
    
    async def update_session_content(
        self, 
        session_id: str, 
        grammar: Optional[str] = None, 
        text: Optional[str] = None,
        settings: Optional[ParseSettings] = None
    ):
        """Update session content."""
        logger.debug(f"Updating content for session {session_id[:8]}...")
        session = await self.get_or_create_session(session_id)
        
        if grammar is not None:
            session.grammar_content = grammar
            logger.debug(f"Updated grammar content ({len(grammar)} chars)")
        if text is not None:
            session.text_content = text
            logger.debug(f"Updated text content ({len(text)} chars)")
        if settings is not None:
            session.parse_settings = settings
            logger.debug(f"Updated parse settings")
        
        session.update_activity()
    
    async def add_websocket_to_session(self, session_id: str, websocket: WebSocket):
        """Add WebSocket connection to session."""
        logger.debug(f"Adding WebSocket to session {session_id[:8]}...")
        session = await self.get_or_create_session(session_id)
        session.add_websocket(websocket)
    
    async def remove_websocket_from_session(self, session_id: str, websocket: WebSocket):
        """Remove WebSocket connection from session."""
        if session_id in self.sessions:
            logger.debug(f"Removing WebSocket from session {session_id[:8]}...")
            self.sessions[session_id].remove_websocket(websocket)
    
    async def broadcast_to_session(self, session_id: str, message: dict):
        """Broadcast message to all WebSocket connections in a session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            # Create a copy of connections set to avoid iteration issues
            connections = list(session.websocket_connections)
            
            logger.debug(f"Broadcasting to session {session_id[:8]}... ({len(connections)} connections)")
            
            disconnected_count = 0
            for websocket in connections:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    # Remove disconnected WebSocket
                    session.remove_websocket(websocket)
                    disconnected_count += 1
                    logger.debug(f"Removed disconnected WebSocket from session {session_id[:8]}...")
            
            if disconnected_count > 0:
                logger.info(f"Removed {disconnected_count} disconnected WebSockets from session {session_id[:8]}...")
    
    def get_session_stats(self) -> Dict[str, int]:
        """Get session statistics."""
        total_connections = sum(
            session.get_connection_count() 
            for session in self.sessions.values()
        )
        
        stats = {
            "total_sessions": len(self.sessions),
            "total_connections": total_connections,
            "active_sessions": len([
                s for s in self.sessions.values() 
                if s.get_connection_count() > 0
            ])
        }
        
        logger.debug(f"Session stats: {stats}")
        return stats
    
    async def shutdown(self):
        """Cleanup on application shutdown."""
        logger.info("Shutting down SessionManager...")
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("SessionManager shutdown complete")


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get global session manager instance."""
    global _session_manager
    if _session_manager is None:
        logger.info("Creating global session manager instance")
        _session_manager = SessionManager()
    return _session_manager