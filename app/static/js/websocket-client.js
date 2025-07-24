/**
 * WebSocket client for real-time communication with the server
 */

export class WebSocketClient {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        // Event callbacks
        this.onConnectCallback = null;
        this.onDisconnectCallback = null;
        this.onParseResultCallback = null;
        this.onParseErrorCallback = null;
        this.onSessionInfoCallback = null;
        this.onErrorCallback = null;
    }
    
    async connect(sessionId) {
        this.sessionId = sessionId;
        return this.establishConnection();
    }
    
    establishConnection() {
        return new Promise((resolve, reject) => {
            try {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/parsing`;
                
                console.log(`Connecting to WebSocket: ${wsUrl}`);
                this.socket = new WebSocket(wsUrl);
                
                this.socket.onopen = () => {
                    console.log('WebSocket connected successfully');
                    this.reconnectAttempts = 0;
                    
                    if (this.onConnectCallback) {
                        this.onConnectCallback();
                    }
                    
                    resolve();
                };
                
                this.socket.onmessage = (event) => {
                    this.handleMessage(event.data);
                };
                
                this.socket.onclose = (event) => {
                    console.log(`WebSocket disconnected: ${event.code} ${event.reason || '(no reason)'}`);
                    
                    if (this.onDisconnectCallback) {
                        this.onDisconnectCallback();
                    }
                    
                    // Attempt reconnection for specific error codes
                    const shouldReconnect = event.code !== 1000 && // Not normal closure
                                          event.code !== 1001 && // Not going away
                                          this.reconnectAttempts < this.maxReconnectAttempts;
                    
                    if (shouldReconnect) {
                        console.log(`Will attempt reconnection (code: ${event.code})`);
                        this.scheduleReconnect();
                    } else {
                        console.log(`Not reconnecting (code: ${event.code}, attempts: ${this.reconnectAttempts})`);
                    }
                };
                
                this.socket.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    // Don't reject immediately - let onclose handle it
                };
                
            } catch (error) {
                console.error('Failed to create WebSocket:', error);
                reject(error);
            }
        });
    }
    
    scheduleReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
        
        setTimeout(() => {
            if (this.socket.readyState === WebSocket.CLOSED) {
                this.establishConnection().catch(console.error);
            }
        }, delay);
    }
    
    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            
            switch (message.type) {
                case 'parse_result':
                    if (this.onParseResultCallback) {
                        this.onParseResultCallback(message.data);
                    }
                    break;
                    
                case 'parse_error':
                    if (this.onParseErrorCallback) {
                        this.onParseErrorCallback(message.data);
                    }
                    break;
                    
                case 'session_info':
                    if (this.onSessionInfoCallback) {
                        this.onSessionInfoCallback(message.data);
                    }
                    break;
                    
                case 'error':
                    if (this.onErrorCallback) {
                        this.onErrorCallback(message.data);
                    }
                    break;
                    
                default:
                    console.warn('Unknown message type:', message.type);
            }
            
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
        }
    }
    
    send(type, data) {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            console.warn('WebSocket not connected, cannot send message');
            return false;
        }
        
        const message = {
            type: type,
            session_id: this.sessionId,
            data: data
        };
        
        try {
            this.socket.send(JSON.stringify(message));
            return true;
        } catch (error) {
            console.error('Failed to send WebSocket message:', error);
            return false;
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.close(1000, 'Client disconnect');
            this.socket = null;
        }
    }
    
    // Event handler setters
    onConnect(callback) {
        this.onConnectCallback = callback;
    }
    
    onDisconnect(callback) {
        this.onDisconnectCallback = callback;
    }
    
    onParseResult(callback) {
        this.onParseResultCallback = callback;
    }
    
    onParseError(callback) {
        this.onParseErrorCallback = callback;
    }
    
    onSessionInfo(callback) {
        this.onSessionInfoCallback = callback;
    }
    
    onError(callback) {
        this.onErrorCallback = callback;
    }
    
    // Connection state
    isConnected() {
        return this.socket && this.socket.readyState === WebSocket.OPEN;
    }
    
    getReadyState() {
        if (!this.socket) return 'CLOSED';
        
        switch (this.socket.readyState) {
            case WebSocket.CONNECTING: return 'CONNECTING';
            case WebSocket.OPEN: return 'OPEN';
            case WebSocket.CLOSING: return 'CLOSING';
            case WebSocket.CLOSED: return 'CLOSED';
            default: return 'UNKNOWN';
        }
    }
}