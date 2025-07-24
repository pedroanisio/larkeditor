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
        
        // Onboarding state
        this.currentOnboardingStep = 1;
        this.onboardingEnabled = !localStorage.getItem('larkeditor-onboarding-disabled');
        this.onboardingShown = false;
        this.connectionTimeout = null;
        
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
            console.log('Attempting WebSocket connection...');
            await this.websocketClient.connect(this.sessionId);
            console.log('WebSocket connection attempt completed');
            
            // Setup editor event handlers
            this.setupEditorHandlers();
            
            // Setup WebSocket event handlers
            this.setupWebSocketHandlers();
            
            // Setup drag & drop for file uploads
            this.setupDragAndDrop();
            
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
        
        document.getElementById('help-button').addEventListener('click', () => {
            this.showOnboardingManual();
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.forceParse();
            }
        });
        
        // Onboarding event handlers
        this.bindOnboardingEvents();
    }
    
    bindOnboardingEvents() {
        // Navigation buttons
        document.getElementById('onboarding-next')?.addEventListener('click', () => {
            this.nextOnboardingStep();
        });
        
        document.getElementById('onboarding-next-2')?.addEventListener('click', () => {
            this.nextOnboardingStep();
        });
        
        document.getElementById('onboarding-next-3')?.addEventListener('click', () => {
            this.nextOnboardingStep();
        });
        
        document.getElementById('onboarding-prev')?.addEventListener('click', () => {
            this.prevOnboardingStep();
        });
        
        document.getElementById('onboarding-prev-2')?.addEventListener('click', () => {
            this.prevOnboardingStep();
        });
        
        document.getElementById('onboarding-prev-3')?.addEventListener('click', () => {
            this.prevOnboardingStep();
        });
        
        // Close and finish buttons
        document.getElementById('onboarding-close')?.addEventListener('click', () => {
            this.closeOnboarding();
        });
        
        document.getElementById('skip-onboarding')?.addEventListener('click', () => {
            this.closeOnboarding();
        });
        
        document.getElementById('onboarding-finish')?.addEventListener('click', () => {
            this.finishOnboarding();
        });
        
        // Step indicators
        document.querySelectorAll('.step-dot').forEach((dot, index) => {
            dot.addEventListener('click', () => {
                this.goToOnboardingStep(index + 1);
            });
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
            console.log('WebSocket connected successfully');
            this.isConnected = true;
            this.updateConnectionStatus(true);
            this.updateStatus('Connected', 'success');
            
            // Clear any existing connection timeout
            if (this.connectionTimeout) {
                clearTimeout(this.connectionTimeout);
                this.connectionTimeout = null;
            }
            
            // Show onboarding wizard for first-time users (only once)
            if (this.onboardingEnabled && !this.onboardingShown) {
                this.onboardingShown = true;
                setTimeout(() => {
                    this.checkAndShowOnboarding();
                }, 1000); // Delay to ensure editors are ready
            }
        });
        
        this.websocketClient.onDisconnect(() => {
            console.log('WebSocket disconnected, updating UI status');
            
            // Use a small delay before marking as disconnected to handle rapid reconnects
            this.connectionTimeout = setTimeout(() => {
                if (!this.websocketClient.isConnected()) {
                    this.isConnected = false;
                    this.updateConnectionStatus(false);
                    this.updateStatus('Disconnected - Reconnecting...', 'warning');
                }
            }, 500);
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
    
    setupDragAndDrop() {
        // Connect drag & drop to editors
        const grammarEditorElement = document.getElementById('grammar-editor');
        const textEditorElement = document.getElementById('text-editor');
        
        // Setup drag & drop for grammar editor
        this.setupElementDragAndDrop(grammarEditorElement, (content, filename) => {
            this.editorManager.setGrammarContent(content);
            this.updateStatus(`Loaded grammar: ${filename}`, 'success');
        }, ['.lark', '.ebnf', '.txt']);
        
        // Setup drag & drop for text editor
        this.setupElementDragAndDrop(textEditorElement, (content, filename) => {
            this.editorManager.setTextContent(content);
            this.updateStatus(`Loaded text: ${filename}`, 'success');
        }, ['.txt']);
    }
    
    setupElementDragAndDrop(element, callback, allowedExtensions) {
        if (!element) return;
        
        element.addEventListener('dragover', (e) => {
            e.preventDefault();
            element.classList.add('drag-over');
        });
        
        element.addEventListener('dragleave', (e) => {
            e.preventDefault();
            element.classList.remove('drag-over');
        });
        
        element.addEventListener('drop', (e) => {
            e.preventDefault();
            element.classList.remove('drag-over');
            
            const files = Array.from(e.dataTransfer.files);
            const file = files[0];
            
            if (file) {
                // Validate file extension
                const isValidExtension = allowedExtensions.some(ext => 
                    file.name.toLowerCase().endsWith(ext)
                );
                
                if (isValidExtension && file.size <= 10 * 1024 * 1024) { // 10MB limit
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        callback(e.target.result, file.name);
                    };
                    reader.onerror = () => {
                        this.updateStatus('Failed to read file', 'error');
                    };
                    reader.readAsText(file);
                } else {
                    const message = !isValidExtension 
                        ? `Invalid file type. Allowed: ${allowedExtensions.join(', ')}`
                        : 'File too large (max 10MB)';
                    this.updateStatus(message, 'error');
                }
            }
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
        const wsConnected = this.websocketClient.isConnected();
        console.log('Force parse triggered, WebSocket state:', this.websocketClient.getReadyState(), 'App connected:', this.isConnected, 'WS connected:', wsConnected);
        
        if (!wsConnected) {
            this.updateStatus('WebSocket not connected - please wait...', 'warning');
            console.warn('WebSocket not ready, connection state:', this.websocketClient.getReadyState());
            
            // Try to reconnect if possible
            if (!this.isConnected) {
                this.updateStatus('Reconnecting...', 'warning');
                setTimeout(() => {
                    if (this.websocketClient.isConnected()) {
                        console.log('Retrying parse after reconnection');
                        this.forceParse();
                    }
                }, 2000);
            }
            return;
        }
        
        this.showLoading(true);
        console.log('Sending force_parse message via WebSocket');
        const sent = this.websocketClient.send('force_parse', {});
        
        if (!sent) {
            this.showLoading(false);
            this.updateStatus('Failed to send parse request', 'error');
            console.error('Failed to send WebSocket message');
        } else {
            console.log('Force parse message sent successfully');
            
            // Add a timeout in case we don't get a response
            setTimeout(() => {
                if (document.getElementById('loading-overlay').classList.contains('hidden')) {
                    return; // Already got response
                }
                this.showLoading(false);
                this.updateStatus('Parse timeout - no response from server', 'error');
            }, 10000); // 10 second timeout
        }
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
    
    // Onboarding Methods
    checkAndShowOnboarding() {
        if (this.onboardingEnabled) {
            console.log('Showing onboarding wizard for first-time user');
            this.showOnboarding();
            this.setDefaultExampleContent();
        }
    }
    
    showOnboarding() {
        document.getElementById('onboarding-overlay').classList.remove('hidden');
        this.goToOnboardingStep(1);
    }
    
    closeOnboarding() {
        const disableCheckbox = document.getElementById('disable-onboarding');
        if (disableCheckbox.checked) {
            localStorage.setItem('larkeditor-onboarding-disabled', 'true');
            this.onboardingEnabled = false;
        }
        document.getElementById('onboarding-overlay').classList.add('hidden');
    }
    
    finishOnboarding() {
        console.log('Onboarding completed successfully');
        this.closeOnboarding();
        
        // Trigger a parse to demonstrate the result
        setTimeout(() => {
            this.forceParse();
        }, 500);
    }
    
    nextOnboardingStep() {
        if (this.currentOnboardingStep < 4) {
            this.goToOnboardingStep(this.currentOnboardingStep + 1);
        }
    }
    
    prevOnboardingStep() {
        if (this.currentOnboardingStep > 1) {
            this.goToOnboardingStep(this.currentOnboardingStep - 1);
        }
    }
    
    goToOnboardingStep(step) {
        // Hide all steps
        document.querySelectorAll('.onboarding-step').forEach(s => s.classList.add('hidden'));
        
        // Show target step
        document.getElementById(`step-${step}`)?.classList.remove('hidden');
        
        // Update step indicators
        document.querySelectorAll('.step-dot').forEach((dot, index) => {
            if (index + 1 === step) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
        
        this.currentOnboardingStep = step;
        
        // Perform step-specific actions
        this.performStepActions(step);
    }
    
    performStepActions(step) {
        switch (step) {
            case 1:
                // Highlight the grammar editor
                this.highlightElement('grammar-editor', 2000);
                break;
            case 2:
                // Highlight the text editor
                this.highlightElement('text-editor', 2000);
                break;
            case 3:
                // Highlight the parse button
                this.highlightElement('force-parse', 3000);
                break;
            case 4:
                // No specific highlighting for feature overview
                break;
        }
    }
    
    highlightElement(elementId, duration = 2000) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.style.boxShadow = '0 0 0 3px rgba(33, 150, 243, 0.5)';
        element.style.transition = 'box-shadow 0.3s ease';
        
        setTimeout(() => {
            element.style.boxShadow = '';
        }, duration);
    }
    
    setDefaultExampleContent() {
        // Set example grammar
        const exampleGrammar = `// Simple arithmetic grammar
start: expr

?expr: term
     | expr "+" term   -> add
     | expr "-" term   -> sub

?term: factor
     | term "*" factor -> mul  
     | term "/" factor -> div

?factor: NUMBER
       | "(" expr ")"

%import common.NUMBER
%import common.WS
%ignore WS`;

        // Set example text
        const exampleText = `2 + 3 * (4 - 1)`;
        
        // Apply to editors when they're ready
        setTimeout(() => {
            if (this.editorManager) {
                console.log('Setting example content for onboarding');
                this.editorManager.setGrammarContent(exampleGrammar);
                this.editorManager.setTextContent(exampleText);
            }
        }, 1000);
    }
    
    // Method to manually show onboarding (for debugging or re-enabling)
    showOnboardingManual() {
        this.onboardingEnabled = true;
        localStorage.removeItem('larkeditor-onboarding-disabled');
        this.showOnboarding();
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.larkEditor = new LarkEditorApp();
    
    // Add global method to re-enable onboarding (for debugging)
    window.showOnboarding = () => {
        window.larkEditor.showOnboardingManual();
    };
});