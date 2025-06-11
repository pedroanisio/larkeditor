/**
 * File upload/download management
 */

export class FileManager {
    constructor() {
        this.setupFileInputs();
    }
    
    setupFileInputs() {
        // Grammar file input
        this.grammarFileInput = document.getElementById('grammar-file-input');
        this.textFileInput = document.getElementById('text-file-input');
        
        if (!this.grammarFileInput) {
            this.grammarFileInput = this.createFileInput('grammar-file-input', '.lark,.ebnf,.txt');
        }
        
        if (!this.textFileInput) {
            this.textFileInput = this.createFileInput('text-file-input', '.txt');
        }
    }
    
    createFileInput(id, accept) {
        const input = document.createElement('input');
        input.type = 'file';
        input.id = id;
        input.accept = accept;
        input.style.display = 'none';
        document.body.appendChild(input);
        return input;
    }
    
    uploadGrammar(callback) {
        this.grammarFileInput.onchange = (event) => {
            const file = event.target.files[0];
            if (file) {
                this.readFile(file, callback);
            }
            // Reset input
            event.target.value = '';
        };
        
        this.grammarFileInput.click();
    }
    
    uploadText(callback) {
        this.textFileInput.onchange = (event) => {
            const file = event.target.files[0];
            if (file) {
                this.readFile(file, callback);
            }
            // Reset input
            event.target.value = '';
        };
        
        this.textFileInput.click();
    }
    
    readFile(file, callback) {
        // Validate file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
            alert('File is too large. Maximum size is 10MB.');
            return;
        }
        
        const reader = new FileReader();
        
        reader.onload = (e) => {
            try {
                const content = e.target.result;
                callback(content, file.name);
            } catch (error) {
                console.error('Failed to read file:', error);
                alert('Failed to read file. Please try again.');
            }
        };
        
        reader.onerror = () => {
            console.error('File reading failed');
            alert('Failed to read file. Please try again.');
        };
        
        reader.readAsText(file);
    }
    
    downloadGrammar(content, filename = 'grammar.lark') {
        this.downloadFile(content, filename, 'text/plain');
    }
    
    downloadText(content, filename = 'test_input.txt') {
        this.downloadFile(content, filename, 'text/plain');
    }
    
    downloadFile(content, filename, contentType = 'text/plain') {
        try {
            const blob = new Blob([content], { type: contentType });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.style.display = 'none';
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            // Clean up the URL object
            setTimeout(() => URL.revokeObjectURL(url), 100);
            
        } catch (error) {
            console.error('Download failed:', error);
            alert('Failed to download file. Please try again.');
        }
    }
    
    async uploadFileToServer(file, fileType = 'grammar') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_type', fileType);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            return result;
            
        } catch (error) {
            console.error('Server upload failed:', error);
            throw error;
        }
    }
    
    async downloadFileFromServer(filename) {
        try {
            const response = await fetch(`/api/download/${encodeURIComponent(filename)}`);
            
            if (!response.ok) {
                throw new Error(`Download failed: ${response.statusText}`);
            }
            
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.style.display = 'none';
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            setTimeout(() => URL.revokeObjectURL(url), 100);
            
        } catch (error) {
            console.error('Server download failed:', error);
            throw error;
        }
    }
    
    // Drag and drop support
    setupDragAndDrop(grammarElement, textElement) {
        [grammarElement, textElement].forEach((element, index) => {
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
                    if (index === 0) {
                        // Grammar editor
                        if (this.isValidGrammarFile(file)) {
                            this.readFile(file, (content, filename) => {
                                // This would need to be connected to the editor
                                console.log('Grammar file dropped:', filename);
                            });
                        } else {
                            alert('Please drop a valid grammar file (.lark, .ebnf, .txt)');
                        }
                    } else {
                        // Text editor
                        if (this.isValidTextFile(file)) {
                            this.readFile(file, (content, filename) => {
                                // This would need to be connected to the editor
                                console.log('Text file dropped:', filename);
                            });
                        } else {
                            alert('Please drop a valid text file (.txt)');
                        }
                    }
                }
            });
        });
    }
    
    isValidGrammarFile(file) {
        const validExtensions = ['.lark', '.ebnf', '.txt'];
        return validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    }
    
    isValidTextFile(file) {
        return file.name.toLowerCase().endsWith('.txt') || 
               file.type.startsWith('text/');
    }
}