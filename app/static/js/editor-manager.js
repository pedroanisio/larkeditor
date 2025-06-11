/**
 * Monaco Editor integration and management
 */

export class EditorManager {
    constructor() {
        this.grammarEditor = null;
        this.textEditor = null;
        this.grammarChangeCallback = null;
        this.textChangeCallback = null;
        this.decorationIds = [];
    }
    
    async init() {
        // Configure Monaco loader
        require.config({ 
            paths: { 
                vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' 
            } 
        });
        
        return new Promise((resolve, reject) => {
            require(['vs/editor/editor.main'], () => {
                try {
                    this.initializeEditors();
                    this.registerLanguages();
                    resolve();
                } catch (error) {
                    reject(error);
                }
            });
        });
    }
    
    initializeEditors() {
        // Grammar editor configuration
        this.grammarEditor = monaco.editor.create(document.getElementById('grammar-editor'), {
            value: this.getDefaultGrammar(),
            language: 'lark',
            theme: 'vs',
            fontSize: 14,
            fontFamily: 'JetBrains Mono, Fira Code, Monaco, Menlo, Ubuntu Mono, monospace',
            lineNumbers: 'on',
            minimap: { enabled: true },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            wordWrap: 'on',
            tabSize: 4,
            insertSpaces: true,
            folding: true,
            bracketMatching: 'always',
            autoIndent: 'full',
            formatOnPaste: true,
            formatOnType: true
        });
        
        // Text editor configuration
        this.textEditor = monaco.editor.create(document.getElementById('text-editor'), {
            value: this.getDefaultText(),
            language: 'plaintext',
            theme: 'vs',
            fontSize: 14,
            fontFamily: 'JetBrains Mono, Fira Code, Monaco, Menlo, Ubuntu Mono, monospace',
            lineNumbers: 'on',
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            wordWrap: 'on',
            tabSize: 2,
            insertSpaces: true
        });
        
        // Setup change listeners with debouncing
        this.setupChangeListeners();
        
        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
    }
    
    registerLanguages() {
        // Register Lark language
        monaco.languages.register({ id: 'lark' });
        
        // Define Lark language tokens
        monaco.languages.setMonarchTokensProvider('lark', {
            tokenizer: {
                root: [
                    // Comments
                    [/\/\/.*$/, 'comment'],
                    [/\/\*/, 'comment', '@comment'],
                    
                    // Rule definitions
                    [/^[a-z_][a-zA-Z0-9_]*\s*:/, 'rule-definition'],
                    
                    // Terminal definitions  
                    [/^[A-Z_][A-Z0-9_]*\s*:/, 'terminal-definition'],
                    
                    // Strings
                    [/"([^"\\\\]|\\\\.)*$/, 'string.invalid'],
                    [/"/, 'string', '@string_double'],
                    [/'([^'\\\\]|\\\\.)*$/, 'string.invalid'],
                    [/'/, 'string', '@string_single'],
                    
                    // Regular expressions
                    [/\/([^\/\\\\]|\\\\.)*\/[gimuy]*/, 'regexp'],
                    
                    // Operators and punctuation
                    [/[{}\\[\\]()]/, 'bracket'],
                    [/[|+*?]/, 'operator'],
                    [/[:;,]/, 'delimiter'],
                    
                    // Keywords
                    [/\\b(start|ignore|import|template)\\b/, 'keyword'],
                    
                    // Rule references
                    [/[a-z_][a-zA-Z0-9_]*/, 'rule-reference'],
                    [/[A-Z_][A-Z0-9_]*/, 'terminal-reference'],
                    
                    // Numbers
                    [/\\d+/, 'number']
                ],
                
                comment: [
                    [/[^\\/*]+/, 'comment'],
                    [/\*\//, 'comment', '@pop'],
                    [/[\\/*]/, 'comment']
                ],
                
                string_double: [
                    [/[^\\\\"]+/, 'string'],
                    [/\\\\./, 'string.escape'],
                    [/"/, 'string', '@pop']
                ],
                
                string_single: [
                    [/[^\\\\']+/, 'string'],
                    [/\\\\./, 'string.escape'],
                    [/'/, 'string', '@pop']
                ]
            }
        });
        
        // Define Lark language configuration
        monaco.languages.setLanguageConfiguration('lark', {
            comments: {
                lineComment: '//',
                blockComment: ['/*', '*/']
            },
            brackets: [
                ['{', '}'],
                ['[', ']'],
                ['(', ')']
            ],
            autoClosingPairs: [
                { open: '{', close: '}' },
                { open: '[', close: ']' },
                { open: '(', close: ')' },
                { open: '"', close: '"' },
                { open: "'", close: "'" }
            ],
            surroundingPairs: [
                { open: '{', close: '}' },
                { open: '[', close: ']' },
                { open: '(', close: ')' },
                { open: '"', close: '"' },
                { open: "'", close: "'" }
            ],
            folding: {
                markers: {
                    start: new RegExp('^\\\\s*#region\\\\b'),
                    end: new RegExp('^\\\\s*#endregion\\\\b')
                }
            }
        });
        
        // Define theme
        monaco.editor.defineTheme('lark-theme', {
            base: 'vs',
            inherit: true,
            rules: [
                { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
                { token: 'rule-definition', foreground: '0000FF', fontStyle: 'bold' },
                { token: 'terminal-definition', foreground: 'AF00DB', fontStyle: 'bold' },
                { token: 'rule-reference', foreground: '001080' },
                { token: 'terminal-reference', foreground: 'A31515' },
                { token: 'string', foreground: 'A31515' },
                { token: 'string.escape', foreground: 'FF0000' },
                { token: 'regexp', foreground: '811F3F' },
                { token: 'operator', foreground: '000000', fontStyle: 'bold' },
                { token: 'keyword', foreground: '0000FF', fontStyle: 'bold' },
                { token: 'number', foreground: '09885A' },
                { token: 'bracket', foreground: '000000' },
                { token: 'delimiter', foreground: '000000' }
            ],
            colors: {
                'editor.background': '#FFFFFF'
            }
        });
        
        // Apply theme
        monaco.editor.setTheme('lark-theme');
    }
    
    setupChangeListeners() {
        let grammarChangeTimer = null;
        let textChangeTimer = null;
        
        // Grammar editor changes with debouncing
        this.grammarEditor.onDidChangeModelContent(() => {
            if (grammarChangeTimer) {
                clearTimeout(grammarChangeTimer);
            }
            
            grammarChangeTimer = setTimeout(() => {
                if (this.grammarChangeCallback) {
                    this.grammarChangeCallback(this.grammarEditor.getValue());
                }
            }, 500); // 500ms debounce
        });
        
        // Text editor changes with debouncing
        this.textEditor.onDidChangeModelContent(() => {
            if (textChangeTimer) {
                clearTimeout(textChangeTimer);
            }
            
            textChangeTimer = setTimeout(() => {
                if (this.textChangeCallback) {
                    this.textChangeCallback(this.textEditor.getValue());
                }
            }, 500); // 500ms debounce
        });
    }
    
    setupKeyboardShortcuts() {
        // Add custom keyboard shortcuts
        this.grammarEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
            // Save grammar
            document.getElementById('download-grammar').click();
        });
        
        this.grammarEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
            // Force parse
            document.getElementById('force-parse').click();
        });
        
        this.textEditor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
            // Save text
            const content = this.textEditor.getValue();
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'test_input.txt';
            a.click();
            URL.revokeObjectURL(url);
        });
    }
    
    getDefaultGrammar() {
        return `// Lark Grammar Example
// Define your grammar rules here

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
    }
    
    getDefaultText() {
        return `// Test input for your grammar
// Enter text to parse here

2 + 3 * (4 - 1)`;
    }
    
    onGrammarChange(callback) {
        this.grammarChangeCallback = callback;
    }
    
    onTextChange(callback) {
        this.textChangeCallback = callback;
    }
    
    getGrammarContent() {
        return this.grammarEditor ? this.grammarEditor.getValue() : '';
    }
    
    getTextContent() {
        return this.textEditor ? this.textEditor.getValue() : '';
    }
    
    setGrammarContent(content) {
        if (this.grammarEditor) {
            this.grammarEditor.setValue(content);
        }
    }
    
    setTextContent(content) {
        if (this.textEditor) {
            this.textEditor.setValue(content);
        }
    }
    
    highlightError(line, column) {
        if (!this.grammarEditor) return;
        
        // Clear previous decorations
        this.grammarEditor.deltaDecorations(this.decorationIds, []);
        
        // Add error decoration
        this.decorationIds = this.grammarEditor.deltaDecorations([], [
            {
                range: new monaco.Range(line, column, line, column + 1),
                options: {
                    className: 'error-decoration',
                    glyphMarginClassName: 'error-glyph',
                    hoverMessage: { value: 'Parse error occurred here' }
                }
            }
        ]);
        
        // Navigate to error
        this.grammarEditor.revealLineInCenter(line);
        this.grammarEditor.setPosition({ lineNumber: line, column: column });
    }
    
    clearErrorHighlights() {
        if (this.grammarEditor) {
            this.grammarEditor.deltaDecorations(this.decorationIds, []);
            this.decorationIds = [];
        }
    }
    
    focus(editor = 'grammar') {
        if (editor === 'grammar' && this.grammarEditor) {
            this.grammarEditor.focus();
        } else if (editor === 'text' && this.textEditor) {
            this.textEditor.focus();
        }
    }
    
    dispose() {
        if (this.grammarEditor) {
            this.grammarEditor.dispose();
        }
        if (this.textEditor) {
            this.textEditor.dispose();
        }
    }
}