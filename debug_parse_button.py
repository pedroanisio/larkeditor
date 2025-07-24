#!/usr/bin/env python3
"""
Debug script to test the parse button functionality step by step.
"""

import asyncio
import json
import websockets
import requests
from datetime import datetime

async def test_websocket_connection():
    """Test WebSocket connection and parse button functionality."""
    print("=== WebSocket Parse Button Debug ===\n")
    
    # Test basic HTTP connection first
    print("1. Testing HTTP connection...")
    try:
        response = requests.get("http://127.0.0.1:8000/api/health")
        print(f"   ✓ HTTP health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ✗ HTTP connection failed: {e}")
        return
    
    # Test WebSocket connection
    print("\n2. Testing WebSocket connection...")
    try:
        uri = "ws://127.0.0.1:8000/ws/parsing"
        async with websockets.connect(uri) as websocket:
            print(f"   ✓ WebSocket connected to {uri}")
            
            # Generate session ID
            session_id = f"debug_session_{int(datetime.now().timestamp())}"
            print(f"   Session ID: {session_id}")
            
            # Test message handling
            print("\n3. Testing message handling...")
            
            # Send grammar content
            grammar_message = {
                "type": "grammar_change",
                "session_id": session_id,
                "data": {
                    "content": "start: expr\nexpr: NUMBER"
                }
            }
            
            await websocket.send(json.dumps(grammar_message))
            print("   ✓ Sent grammar change message")
            
            # Receive session info
            response = await websocket.recv()
            session_info = json.loads(response)
            print(f"   ✓ Received: {session_info['type']}")
            
            # Send text content
            text_message = {
                "type": "text_change", 
                "session_id": session_id,
                "data": {
                    "content": "42"
                }
            }
            
            await websocket.send(json.dumps(text_message))
            print("   ✓ Sent text change message")
            
            # Receive session info
            response = await websocket.recv()
            session_info = json.loads(response)
            print(f"   ✓ Received: {session_info['type']}")
            
            print("\n4. Testing force parse (the actual parse button)...")
            
            # Send force parse message (this simulates clicking the parse button)
            force_parse_message = {
                "type": "force_parse",
                "session_id": session_id,
                "data": {}
            }
            
            await websocket.send(json.dumps(force_parse_message))
            print("   ✓ Sent force_parse message (simulating parse button click)")
            
            # Wait for multiple responses
            responses_received = 0
            timeout_count = 0
            max_timeout = 3
            
            while responses_received < 2 and timeout_count < max_timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    message = json.loads(response)
                    responses_received += 1
                    
                    print(f"   ✓ Response {responses_received}: {message['type']}")
                    
                    if message['type'] == 'parse_result':
                        print(f"      Status: {message['data']['status']}")
                        if message['data']['status'] == 'success':
                            print("      ✓ Parse succeeded!")
                        else:
                            print(f"      ✗ Parse failed: {message['data'].get('error', 'Unknown error')}")
                    elif message['type'] == 'parse_error':
                        print(f"      ✗ Parse error: {message['data']}")
                    elif message['type'] == 'session_info':
                        print(f"      Session connections: {message['data']['connection_count']}")
                        print(f"      Has grammar: {message['data']['has_grammar']}")
                        print(f"      Has text: {message['data']['has_text']}")
                    
                except asyncio.TimeoutError:
                    timeout_count += 1
                    print(f"   ! Timeout {timeout_count}/{max_timeout} waiting for response")
            
            if responses_received == 0:
                print("   ✗ No responses received - parse button not working!")
            else:
                print(f"   ✓ Received {responses_received} responses")
                
    except Exception as e:
        print(f"   ✗ WebSocket test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Make sure the FastAPI server is running on http://127.0.0.1:8000")
    print("Run: python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000\n")
    
    try:
        asyncio.run(test_websocket_connection())
    except KeyboardInterrupt:
        print("\nDebug interrupted by user")