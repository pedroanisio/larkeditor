"""WebSocket handlers for real-time parsing updates."""

import asyncio
import json
from typing import Dict, Optional
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError

from ..models.requests import ParseSettings, ParserType
from ..models.responses import WebSocketMessage, ParseResult
from ..core.parser import get_parser
from ..core.state import get_session_manager
from ..core.config import get_settings, get_logger

router = APIRouter()
settings = get_settings()
logger = get_logger("websocket")


class WSMessageType:
    """WebSocket message types."""
    GRAMMAR_CHANGE = "grammar_change"
    TEXT_CHANGE = "text_change"
    SETTINGS_CHANGE = "settings_change"
    FORCE_PARSE = "force_parse"
    PARSE_RESULT = "parse_result"
    PARSE_ERROR = "parse_error"
    SESSION_INFO = "session_info"
    ERROR = "error"


class ContentChangeData(BaseModel):
    """Data for content change messages."""
    content: str


class SettingsChangeData(BaseModel):
    """Data for settings change messages."""
    parser: Optional[ParserType] = None
    start_rule: Optional[str] = None
    debug: Optional[bool] = None


class IncomingMessage(BaseModel):
    """Incoming WebSocket message structure."""
    type: str
    session_id: str
    data: Dict


class ParseManager:
    """Manages debounced parsing operations."""
    
    def __init__(self):
        self.parse_timers: Dict[str, asyncio.Task] = {}
        self.debounce_delay = settings.debounce_delay
        logger.info(f"Initialized ParseManager with debounce_delay={self.debounce_delay}s")
    
    async def handle_content_change(
        self, 
        session_id: str, 
        grammar: str, 
        text: str, 
        parse_settings: ParseSettings
    ):
        """Handle content change with debouncing."""
        logger.debug(f"Content change for session {session_id[:8]}... grammar({len(grammar)}), text({len(text)})")
        
        # Cancel existing timer
        if session_id in self.parse_timers:
            self.parse_timers[session_id].cancel()
            logger.debug(f"Cancelled existing parse timer for session {session_id[:8]}...")
        
        # Create new debounced parse task
        self.parse_timers[session_id] = asyncio.create_task(
            self._debounced_parse(session_id, grammar, text, parse_settings)
        )
        logger.debug(f"Started debounced parse task for session {session_id[:8]}...")
    
    async def _debounced_parse(
        self, 
        session_id: str, 
        grammar: str, 
        text: str, 
        parse_settings: ParseSettings
    ):
        """Execute parsing after debounce delay."""
        try:
            logger.debug(f"Debounced parse waiting {self.debounce_delay}s for session {session_id[:8]}...")
            await asyncio.sleep(self.debounce_delay)
            
            logger.info(f"Executing debounced parse for session {session_id[:8]}...")
            
            # Perform the actual parsing
            parser = get_parser()
            result = await parser.parse_async(grammar, text, parse_settings)
            
            # Update session with result
            session_manager = get_session_manager()
            session = await session_manager.get_or_create_session(session_id)
            session.last_parse_result = result
            
            # Broadcast result to all connections in session
            message = {
                "type": WSMessageType.PARSE_RESULT,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "data": result.dict()
            }
            
            logger.info(f"Broadcasting parse result to session {session_id[:8]}... (status: {result.status})")
            await session_manager.broadcast_to_session(session_id, message)
            
        except asyncio.CancelledError:
            # Task was cancelled (new content change), ignore
            logger.debug(f"Debounced parse cancelled for session {session_id[:8]}...")
            pass
        except Exception as e:
            # Send error message
            logger.error(f"Debounced parse failed for session {session_id[:8]}...: {str(e)}")
            session_manager = get_session_manager()
            error_message = {
                "type": WSMessageType.PARSE_ERROR,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "error": str(e),
                    "error_type": "parsing_error"
                }
            }
            await session_manager.broadcast_to_session(session_id, error_message)
        finally:
            # Clean up timer
            if session_id in self.parse_timers:
                del self.parse_timers[session_id]
                logger.debug(f"Cleaned up parse timer for session {session_id[:8]}...")


# Global parse manager
parse_manager = ParseManager()


@router.websocket("/parsing")
async def websocket_parsing_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time parsing updates."""
    client_host = websocket.client.host if websocket.client else "unknown"
    logger.info(f"New WebSocket connection from {client_host}")
    
    await websocket.accept()
    session_manager = get_session_manager()
    current_session_id: Optional[str] = None
    message_count = 0
    
    try:
        while True:
            # Receive message
            logger.debug("Waiting for WebSocket message...")
            data = await websocket.receive_text()
            message_count += 1
            
            logger.debug(f"Received WebSocket message #{message_count} ({len(data)} chars)")
            
            try:
                # Parse incoming message
                message_data = json.loads(data)
                message = IncomingMessage(**message_data)
                
                logger.info(f"Processing message type '{message.type}' for session {message.session_id[:8]}...")
                
                # Update current session
                if current_session_id != message.session_id:
                    # Remove from old session
                    if current_session_id:
                        logger.debug(f"Removing WebSocket from old session {current_session_id[:8]}...")
                        await session_manager.remove_websocket_from_session(
                            current_session_id, websocket
                        )
                    
                    # Add to new session
                    current_session_id = message.session_id
                    logger.debug(f"Adding WebSocket to new session {current_session_id[:8]}...")
                    await session_manager.add_websocket_to_session(
                        current_session_id, websocket
                    )
                
                # Get session
                session = await session_manager.get_or_create_session(message.session_id)
                
                # Handle different message types
                if message.type == WSMessageType.GRAMMAR_CHANGE:
                    content_data = ContentChangeData(**message.data)
                    logger.debug(f"Grammar change: {len(content_data.content)} chars")
                    session.grammar_content = content_data.content
                    
                    # Trigger parsing if we have both grammar and text
                    if session.text_content:
                        logger.debug("Triggering parse (grammar + text available)")
                        await parse_manager.handle_content_change(
                            message.session_id,
                            session.grammar_content,
                            session.text_content,
                            session.parse_settings
                        )
                    else:
                        logger.debug("No text content available, skipping parse")
                
                elif message.type == WSMessageType.TEXT_CHANGE:
                    content_data = ContentChangeData(**message.data)
                    logger.debug(f"Text change: {len(content_data.content)} chars")
                    session.text_content = content_data.content
                    
                    # Trigger parsing if we have both grammar and text
                    if session.grammar_content:
                        logger.debug("Triggering parse (text + grammar available)")
                        await parse_manager.handle_content_change(
                            message.session_id,
                            session.grammar_content,
                            session.text_content,
                            session.parse_settings
                        )
                    else:
                        logger.debug("No grammar content available, skipping parse")
                
                elif message.type == WSMessageType.SETTINGS_CHANGE:
                    settings_data = SettingsChangeData(**message.data)
                    logger.debug(f"Settings change: parser={settings_data.parser}, start_rule={settings_data.start_rule}, debug={settings_data.debug}")
                    
                    # Update settings
                    if settings_data.parser is not None:
                        session.parse_settings.parser = settings_data.parser
                    if settings_data.start_rule is not None:
                        session.parse_settings.start_rule = settings_data.start_rule
                    if settings_data.debug is not None:
                        session.parse_settings.debug = settings_data.debug
                    
                    # Trigger parsing if we have content
                    if session.grammar_content and session.text_content:
                        logger.debug("Triggering parse after settings change")
                        await parse_manager.handle_content_change(
                            message.session_id,
                            session.grammar_content,
                            session.text_content,
                            session.parse_settings
                        )
                
                elif message.type == WSMessageType.FORCE_PARSE:
                    logger.info(f"Force parse requested for session {message.session_id[:8]}...")
                    # Force immediate parsing
                    if session.grammar_content and session.text_content:
                        # Cancel any existing debounced parsing
                        if message.session_id in parse_manager.parse_timers:
                            parse_manager.parse_timers[message.session_id].cancel()
                            logger.debug("Cancelled existing debounced parse")
                        
                        # Parse immediately
                        logger.debug("Executing immediate parse...")
                        parser = get_parser()
                        result = await parser.parse_async(
                            session.grammar_content,
                            session.text_content,
                            session.parse_settings
                        )
                        
                        session.last_parse_result = result
                        
                        # Send result
                        response = {
                            "type": WSMessageType.PARSE_RESULT,
                            "session_id": message.session_id,
                            "timestamp": datetime.now().isoformat(),
                            "data": result.dict()
                        }
                        logger.info(f"Sending immediate parse result (status: {result.status})")
                        await websocket.send_json(response)
                    else:
                        logger.warning("Force parse requested but missing grammar or text content")
                
                # Send session info
                session_info = {
                    "type": WSMessageType.SESSION_INFO,
                    "session_id": message.session_id,
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "session_id": session.session_id,
                        "connection_count": session.get_connection_count(),
                        "has_grammar": bool(session.grammar_content),
                        "has_text": bool(session.text_content),
                        "settings": session.parse_settings.dict()
                    }
                }
                logger.debug(f"Sending session info: connections={session.get_connection_count()}")
                await websocket.send_json(session_info)
                
            except ValidationError as e:
                # Send validation error
                logger.error(f"Message validation error: {str(e)}")
                error_response = {
                    "type": WSMessageType.ERROR,
                    "session_id": current_session_id or "unknown",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "error": "Invalid message format",
                        "details": str(e)
                    }
                }
                await websocket.send_json(error_response)
            
            except json.JSONDecodeError as e:
                # Send JSON error
                logger.error(f"JSON decode error: {str(e)}")
                error_response = {
                    "type": WSMessageType.ERROR,
                    "session_id": current_session_id or "unknown",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "error": "Invalid JSON format"
                    }
                }
                await websocket.send_json(error_response)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {current_session_id[:8] if current_session_id else 'unknown'} after {message_count} messages")
    except Exception as e:
        logger.error(f"WebSocket error for session {current_session_id[:8] if current_session_id else 'unknown'}: {str(e)}")
    finally:
        # Clean up on disconnect
        if current_session_id:
            logger.debug(f"Cleaning up WebSocket for session {current_session_id[:8]}...")
            await session_manager.remove_websocket_from_session(
                current_session_id, websocket
            )