/**
 * Main application entry point for LarkEditor Web
 */

import { EditorManager } from './editor-manager.js';
import { WebSocketClient } from './websocket-client.js';
import { FileManager } from './file-manager.js';
import { ASTRenderer } from './ast-renderer.js';

class LarkEditorApp {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.isConnected = false;
        this.parseDebounceTimer = null;
        
        // Initialize components
        this.editorManager = new EditorManager();
        this.websocketClient = new WebSocketClient();
        this.fileManager = new FileManager();
        this.astRenderer = new ASTRenderer();
        
        // Bind event handlers
        this.bindEvents();
        
        // Initialize application
        this.init();
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    async init() {
        try {
            // Update session info in UI
            document.getElementById('session-id').textContent = `Session: ${this.sessionId.slice(-8)}`;
            
            // Initialize Monaco Editor
            await this.editorManager.init();
            
            // Connect WebSocket
            await this.websocketClient.connect(this.sessionId);
            
            // Setup editor event handlers
            this.setupEditorHandlers();
            
            // Setup WebSocket event handlers
            this.setupWebSocketHandlers();
            
            // Update status
            this.updateStatus('Ready');
            
        } catch (error) {
            console.error('Application initialization failed:', error);
            this.updateStatus('Initialization failed', 'error');
        }
    }
    
    bindEvents() {
        // Parse button
        document.getElementById('force-parse').addEventListener('click', () => {
            this.forceParse();
        });
        
        // Settings changes
        document.getElementById('parser-type').addEventListener('change', (e) => {
            this.onSettingsChange();
        });
        
        document.getElementById('start-rule').addEventListener('input', (e) => {
            this.onSettingsChange();
        });
        
        document.getElementById('debug-mode').addEventListener('change', (e) => {
            this.onSettingsChange();
        });
        
        // File operations
        document.getElementById('upload-grammar').addEventListener('click', () => {
            this.fileManager.uploadGrammar((content, filename) => {
                this.editorManager.setGrammarContent(content);
                this.updateStatus(`Loaded ${filename}`, 'success');
            });
        });
        
        document.getElementById('download-grammar').addEventListener('click', () => {
            const content = this.editorManager.getGrammarContent();
            this.fileManager.downloadGrammar(content);
        });
        
        document.getElementById('upload-text').addEventListener('click', () => {
            this.fileManager.uploadText((content, filename) => {
                this.editorManager.setTextContent(content);
                this.updateStatus(`Loaded ${filename}`, 'success');
            });
        });
        
        document.getElementById('export-results').addEventListener('click', () => {
            this.exportResults();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.forceParse();
            }
        });
    }
    
    setupEditorHandlers() {
        // Grammar editor changes
        this.editorManager.onGrammarChange((content) => {
            this.updateGrammarInfo(content);
            this.sendContentChange('grammar', content);
        });
        
        // Text editor changes
        this.editorManager.onTextChange((content) => {
            this.updateTextInfo(content);
            this.sendContentChange('text', content);
        });
    }
    
    setupWebSocketHandlers() {
        this.websocketClient.onConnect(() => {
            this.isConnected = true;
            this.updateConnectionStatus(true);
            this.updateStatus('Connected', 'success');
        });
        
        this.websocketClient.onDisconnect(() => {
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.updateStatus('Disconnected', 'error');
        });
        
        this.websocketClient.onParseResult((result) => {
            this.handleParseResult(result);
        });
        
        this.websocketClient.onParseError((error) => {
            this.handleParseError(error);
        });
        
        this.websocketClient.onSessionInfo((info) => {
            this.handleSessionInfo(info);
        });
        
        this.websocketClient.onError((error) => {
            console.error('WebSocket error:', error);
            this.updateStatus(`Error: ${error.error}`, 'error');
        });
    }
    
    sendContentChange(type, content) {
        if (!this.isConnected) return;
        
        const messageType = type === 'grammar' ? 'grammar_change' : 'text_change';
        this.websocketClient.send(messageType, { content });
    }
    
    onSettingsChange() {
        if (!this.isConnected) return;
        
        const settings = {
            parser: document.getElementById('parser-type').value,
            start_rule: document.getElementById('start-rule').value || 'start',
            debug: document.getElementById('debug-mode').checked
        };
        
        this.websocketClient.send('settings_change', settings);
    }
    
    forceParse() {
        if (!this.isConnected) return;
        
        this.showLoading(true);
        this.websocketClient.send('force_parse', {});
    }
    
    handleParseResult(result) {
        this.showLoading(false);
        
        if (result.status === 'success' && result.tree) {
            // Display AST tree
            this.astRenderer.render(result.tree, document.getElementById('ast-tree'));
            
            // Hide error display
            document.getElementById('error-display').classList.add('hidden');
            document.getElementById('ast-tree').classList.remove('hidden');
            
            // Update status
            this.updateParseStatus('Parsed successfully', 'success', result.parse_time);
            
        } else if (result.error) {
            this.handleParseError(result.error);
        }
    }
    
    handleParseError(error) {
        this.showLoading(false);
        
        // Hide AST tree
        document.getElementById('ast-tree').classList.add('hidden');
        
        // Show error display
        const errorDisplay = document.getElementById('error-display');
        errorDisplay.classList.remove('hidden');
        
        // Update error information
        document.getElementById('error-type').textContent = error.type || 'Error';
        
        const location = error.line && error.column 
            ? `Line ${error.line}, Column ${error.column}`
            : '';
        document.getElementById('error-location').textContent = location;
        
        document.getElementById('error-message').textContent = error.message || 'Unknown error';
        
        // Show suggestions if available
        const suggestionsEl = document.getElementById('error-suggestions');
        if (error.suggestions && error.suggestions.length > 0) {
            suggestionsEl.innerHTML = `
                <h4>Suggestions:</h4>
                <ul>
                    ${error.suggestions.map(s => `<li>${s}</li>`).join('')}
                </ul>
            `;
            suggestionsEl.style.display = 'block';
        } else {
            suggestionsEl.style.display = 'none';
        }
        
        // Update status
        this.updateParseStatus('Parse failed', 'error');
        
        // Highlight error location in editor if available
        if (error.line && error.column) {
            this.editorManager.highlightError(error.line, error.column);
        }
    }
    
    handleSessionInfo(info) {
        // Update connection count or other session info if needed
        console.log('Session info:', info);
    }
    
    updateGrammarInfo(content) {
        const lines = content.split('\n').length;
        document.getElementById('grammar-lines').textContent = `${lines} lines`;
        
        // Update grammar status
        const status = content.trim() ? 'Modified' : 'Empty';
        document.getElementById('grammar-status').textContent = status;
    }
    
    updateTextInfo(content) {
        const lines = content.split('\n').length;
        document.getElementById('text-lines').textContent = `${lines} lines`;
    }
    
    updateParseStatus(message, type = 'info', parseTime = null) {
        const statusEl = document.getElementById('parse-status');
        statusEl.textContent = message;
        statusEl.className = `status-text ${type}`;
        
        if (parseTime !== null) {
            document.getElementById('parse-time').textContent = `${(parseTime * 1000).toFixed(1)}ms`;
        }
    }
    
    updateConnectionStatus(connected) {
        const indicators = document.querySelectorAll('.status-indicator, .connection-status');
        indicators.forEach(indicator => {
            if (connected) {
                indicator.classList.remove('disconnected', 'connecting');
                indicator.classList.add('connected');
            } else {
                indicator.classList.remove('connected', 'connecting');
                indicator.classList.add('disconnected');
            }
        });
    }
    
    updateStatus(message, type = 'info') {
        document.getElementById('status-text').textContent = message;
    }
    
    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }
    
    async exportResults() {
        try {
            const format = 'json'; // Could be made configurable
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    format: format,
                    session_id: this.sessionId,
                    include_metadata: true
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                this.fileManager.downloadFile(result.content, result.filename, result.content_type);
                this.updateStatus('Results exported', 'success');
            } else {
                throw new Error('Export failed');
            }
            
        } catch (error) {
            console.error('Export error:', error);
            this.updateStatus('Export failed', 'error');
        }
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.larkEditor = new LarkEditorApp();
});