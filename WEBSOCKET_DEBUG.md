# WebSocket Connection Debugging Guide

## 🔍 Current Issue Analysis

**Symptoms:**
- WebSocket connects successfully but immediately disconnects with error code 1012
- Connection status tracking shows `false` when parse button is clicked
- Parse operations fail with "WebSocket not connected" error

**Error Code 1012:** Service Restart - indicates the server is restarting or terminating the connection

## 🛠️ Debugging Steps

### 1. Test Backend Directly
```bash
cd /home/pals/code/grammar/larkeditor
python test_parsing.py
```
This tests the parser without WebSocket to isolate the issue.

### 2. Check Server Logs
Look for these patterns in the server logs:
```
INFO: WebSocket connection accepted for [client]
ERROR: Failed to accept WebSocket connection: [error]
INFO: Force parse requested for session [id]
ERROR: Force parse failed: [error]
```

### 3. Browser Network Tab
1. Open Developer Tools (F12)
2. Go to Network tab
3. Filter by "WS" (WebSocket)
4. Refresh page and watch the WebSocket connection
5. Look for:
   - Connection establishment (status 101)
   - Immediate disconnection
   - Error messages in the connection log

### 4. WebSocket Connection Test
In browser console:
```javascript
// Test raw WebSocket connection
const ws = new WebSocket(`ws://${window.location.host}/ws/parsing`);
ws.onopen = () => console.log('✅ Raw WebSocket connected');
ws.onclose = (e) => console.log('❌ Raw WebSocket closed:', e.code, e.reason);
ws.onerror = (e) => console.log('🚫 Raw WebSocket error:', e);

// Test sending a message
ws.onopen = () => {
    console.log('Sending test message...');
    ws.send(JSON.stringify({
        type: 'force_parse',
        session_id: 'test_123',
        data: {}
    }));
};
```

## 🔧 Potential Fixes

### Fix 1: Server Configuration
The issue might be related to the server binding to `10.10.10.187` instead of `0.0.0.0` or `127.0.0.1`.

**Check current config:**
```python
# In app/core/config.py
host: str = "10.10.10.187"  # This might be the issue
```

**Try changing to:**
```python
host: str = "0.0.0.0"  # Bind to all interfaces
# or
host: str = "127.0.0.1"  # Local only
```

### Fix 2: WebSocket Headers
Add proper WebSocket headers in the backend:

```python
# In app/websockets/parsing_ws.py
@router.websocket("/parsing")
async def websocket_parsing_endpoint(websocket: WebSocket):
    # Check WebSocket headers
    headers = dict(websocket.headers)
    logger.info(f"WebSocket headers: {headers}")
    
    await websocket.accept()
    # ... rest of the code
```

### Fix 3: CORS/Origin Issues
Add CORS configuration for WebSocket:

```python
# In app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, be more specific
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Fix 4: WebSocket Endpoint Path
Make sure the WebSocket endpoint is properly registered:

```python
# Check app/main.py includes:
app.include_router(parsing_ws.router, prefix="/ws", tags=["websockets"])
```

## 🧪 Quick Test Commands

### Test 1: Backend Parser
```bash
python test_parsing.py
```

### Test 2: Server Start with Debug
```bash
python -c "
from app.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000, log_level='debug')
"
```

### Test 3: Direct WebSocket Test
```bash
# Install wscat if not available
npm install -g wscat

# Test WebSocket connection
wscat -c ws://10.10.10.187:8000/ws/parsing
```

### Test 4: Browser Console Tests
```javascript
// Test application components
console.log('App:', window.larkEditor);
console.log('WebSocket state:', window.larkEditor.websocketClient.getReadyState());
console.log('Connection status:', window.larkEditor.isConnected);

// Force reconnection
window.larkEditor.websocketClient.connect(window.larkEditor.sessionId);

// Test parse function
window.larkEditor.forceParse();
```

## 🎯 Most Likely Solutions

1. **Change server host to `0.0.0.0`** in config
2. **Check firewall/network** blocking WebSocket connections
3. **Add WebSocket-specific logging** to identify connection drops
4. **Test with different browsers** to rule out browser issues

## 📋 Debugging Checklist

- [ ] Backend parser works independently
- [ ] Server logs show WebSocket acceptance
- [ ] Browser network tab shows WebSocket connection
- [ ] No CORS errors in browser console
- [ ] Server host binding is correct
- [ ] WebSocket URL is accessible
- [ ] No proxy/firewall blocking connections
- [ ] WebSocket messages are properly formatted

## 🚨 Emergency Fallback

If WebSocket continues to fail, implement HTTP polling as a fallback:

```javascript
// In app.js, add polling fallback
if (!this.websocketClient.isConnected()) {
    console.log('WebSocket failed, using HTTP fallback');
    this.useHttpPolling = true;
    this.startHttpPolling();
}
```

This ensures the application works even with WebSocket issues.