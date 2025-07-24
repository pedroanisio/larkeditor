/**
 * AST tree rendering and visualization
 */

export class ASTRenderer {
    constructor() {
        this.expandedNodes = new Set();
    }
    
    render(astNode, container) {
        if (!astNode || !container) return;
        
        // Clear container
        container.innerHTML = '';
        
        // Create tree structure
        const treeElement = this.createTreeElement(astNode, []);
        container.appendChild(treeElement);
        
        // Setup event listeners
        this.setupEventListeners(container);
    }
    
    createTreeElement(node, path) {
        const nodeElement = document.createElement('div');
        nodeElement.className = 'ast-node';
        nodeElement.dataset.path = path.join('.');
        
        if (node.type === 'tree') {
            // Tree node
            nodeElement.classList.add('tree-node');
            
            const hasChildren = node.children && node.children.length > 0;
            const isExpanded = this.expandedNodes.has(path.join('.'));
            
            // Toggle button
            const toggleElement = document.createElement('span');
            toggleElement.className = 'ast-toggle';
            toggleElement.textContent = hasChildren ? (isExpanded ? '▼' : '▶') : '●';
            
            // Content
            const contentElement = document.createElement('span');
            contentElement.className = 'ast-content';
            contentElement.textContent = node.data;
            
            nodeElement.appendChild(toggleElement);
            nodeElement.appendChild(contentElement);
            
            // Children container
            if (hasChildren) {
                const childrenElement = document.createElement('div');
                childrenElement.className = 'ast-children';
                
                if (isExpanded) {
                    nodeElement.classList.add('expanded');
                    childrenElement.style.display = 'block';
                } else {
                    nodeElement.classList.add('collapsed');
                    childrenElement.style.display = 'none';
                }
                
                // Render children
                node.children.forEach((child, index) => {
                    const childPath = [...path, index];
                    const childElement = this.createTreeElement(child, childPath);
                    childrenElement.appendChild(childElement);
                });
                
                nodeElement.appendChild(childrenElement);
            }
            
        } else {
            // Token node
            nodeElement.classList.add('token-node');
            
            // Token content
            const contentElement = document.createElement('span');
            contentElement.className = 'ast-content';
            contentElement.textContent = `"${this.escapeString(node.data)}"`;
            
            nodeElement.appendChild(contentElement);
            
            // Position information
            if (node.line !== null && node.column !== null) {
                const positionElement = document.createElement('span');
                positionElement.className = 'ast-position';
                positionElement.textContent = `${node.line}:${node.column}`;
                nodeElement.appendChild(positionElement);
            }
        }
        
        return nodeElement;
    }
    
    setupEventListeners(container) {
        container.addEventListener('click', (e) => {
            const nodeElement = e.target.closest('.ast-node');
            if (!nodeElement) return;
            
            const toggleElement = nodeElement.querySelector('.ast-toggle');
            if (!toggleElement || e.target !== toggleElement) return;
            
            this.toggleNode(nodeElement);
        });
    }
    
    toggleNode(nodeElement) {
        const path = nodeElement.dataset.path;
        const childrenElement = nodeElement.querySelector('.ast-children');
        const toggleElement = nodeElement.querySelector('.ast-toggle');
        
        if (!childrenElement || !toggleElement) return;
        
        const isExpanded = nodeElement.classList.contains('expanded');
        
        if (isExpanded) {
            // Collapse
            nodeElement.classList.remove('expanded');
            nodeElement.classList.add('collapsed');
            childrenElement.style.display = 'none';
            toggleElement.textContent = '▶';
            this.expandedNodes.delete(path);
        } else {
            // Expand
            nodeElement.classList.remove('collapsed');
            nodeElement.classList.add('expanded');
            childrenElement.style.display = 'block';
            toggleElement.textContent = '▼';
            this.expandedNodes.add(path);
        }
    }
    
    expandAll(container) {
        const treeNodes = container.querySelectorAll('.ast-node.tree-node');
        treeNodes.forEach(node => {
            const childrenElement = node.querySelector('.ast-children');
            const toggleElement = node.querySelector('.ast-toggle');
            
            if (childrenElement && toggleElement) {
                node.classList.remove('collapsed');
                node.classList.add('expanded');
                childrenElement.style.display = 'block';
                toggleElement.textContent = '▼';
                this.expandedNodes.add(node.dataset.path);
            }
        });
    }
    
    collapseAll(container) {
        const treeNodes = container.querySelectorAll('.ast-node.tree-node');
        treeNodes.forEach(node => {
            const childrenElement = node.querySelector('.ast-children');
            const toggleElement = node.querySelector('.ast-toggle');
            
            if (childrenElement && toggleElement) {
                node.classList.remove('expanded');
                node.classList.add('collapsed');
                childrenElement.style.display = 'none';
                toggleElement.textContent = '▶';
                this.expandedNodes.delete(node.dataset.path);
            }
        });
    }
    
    findNode(container, searchText) {
        const allNodes = container.querySelectorAll('.ast-content');
        const matches = [];
        
        allNodes.forEach(node => {
            if (node.textContent.toLowerCase().includes(searchText.toLowerCase())) {
                matches.push(node.closest('.ast-node'));
            }
        });
        
        return matches;
    }
    
    highlightNode(nodeElement) {
        // Remove previous highlights
        const container = nodeElement.closest('.ast-tree');
        if (container) {
            container.querySelectorAll('.ast-node.highlighted').forEach(node => {
                node.classList.remove('highlighted');
            });
        }
        
        // Add highlight
        nodeElement.classList.add('highlighted');
        
        // Scroll into view
        nodeElement.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }
    
    exportTree(astNode, format = 'json') {
        switch (format) {
            case 'json':
                return JSON.stringify(astNode, null, 2);
                
            case 'xml':
                return this.toXML(astNode);
                
            case 'dot':
                return this.toDOT(astNode);
                
            case 'text':
                return this.toText(astNode);
                
            default:
                throw new Error(`Unsupported export format: ${format}`);
        }
    }
    
    toXML(node, depth = 0) {
        const indent = '  '.repeat(depth);
        
        if (node.type === 'tree') {
            let xml = `${indent}<tree data="${this.escapeXML(node.data)}">\\n`;
            
            if (node.children) {
                node.children.forEach(child => {
                    xml += this.toXML(child, depth + 1);
                });
            }
            
            xml += `${indent}</tree>\\n`;
            return xml;
        } else {
            let xml = `${indent}<token data="${this.escapeXML(node.data)}"`;
            
            if (node.line !== null && node.column !== null) {
                xml += ` line="${node.line}" column="${node.column}" />\\n`;
            } else {
                xml += ` />\\n`;
            }
            return xml;
        }
    }
    
    toDOT(node, nodeId = 0) {
        let dot = nodeId === 0 ? 'digraph AST {\\n' : '';
        let nextId = nodeId + 1;
        
        if (node.type === 'tree') {
            dot += `  ${nodeId} [label="${this.escapeDOT(node.data)}" shape=ellipse];\\n`;
            
            if (node.children) {
                node.children.forEach(child => {
                    dot += `  ${nodeId} -> ${nextId};\\n`;
                    const result = this.toDOT(child, nextId);
                    dot += result.dot;
                    nextId = result.nextId;
                });
            }
        } else {
            const label = `"${this.escapeDOT(node.data)}"`;
            dot += `  ${nodeId} [label=${label} shape=box];\\n`;
        }
        
        if (nodeId === 0) {
            dot += '}\\n';
            return dot;
        } else {
            return { dot: dot, nextId: nextId };
        }
    }
    
    toText(node, depth = 0) {
        const indent = '  '.repeat(depth);
        
        if (node.type === 'tree') {
            let text = `${indent}${node.data}\\n`;
            
            if (node.children) {
                node.children.forEach(child => {
                    text += this.toText(child, depth + 1);
                });
            }
            
            return text;
        } else {
            const position = node.line !== null && node.column !== null 
                ? ` (${node.line}:${node.column})`
                : '';
            return `${indent}"${this.escapeString(node.data)}"${position}\\n`;
        }
    }
    
    escapeString(str) {
        return str
            .replace(/\\\\/g, '\\\\\\\\')
            .replace(/"/g, '\\\\"')
            .replace(/\\n/g, '\\\\n')
            .replace(/\\r/g, '\\\\r')
            .replace(/\\t/g, '\\\\t');
    }
    
    escapeXML(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
    
    escapeDOT(str) {
        return str
            .replace(/\\\\/g, '\\\\\\\\')
            .replace(/"/g, '\\\\"')
            .replace(/\\n/g, '\\\\n');
    }
}