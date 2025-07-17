// Fusion Chat Interface JavaScript
class FusionChatApp {
    constructor() {
        this.websocket = null;
        this.currentModel = 'hybrid-fusion-v1';
        this.conversationId = null;
        this.isConnected = false;
        
        this.elements = {
            chatHistory: document.getElementById('chatHistory'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            modelSelect: document.getElementById('modelSelect'),
            statusBtn: document.getElementById('statusBtn'),
            clearBtn: document.getElementById('clearBtn'),
            charCount: document.getElementById('charCount'),
            connectionStatus: document.getElementById('connectionStatus'),
            systemStatus: document.getElementById('systemStatus'),
            modelsList: document.getElementById('modelsList'),
            conversationsList: document.getElementById('conversationsList'),
            statusModal: document.getElementById('statusModal'),
            detailedStatus: document.getElementById('detailedStatus')
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.loadModels();
        this.loadSystemStatus();
        this.loadConversations();
        
        // Start periodic updates
        setInterval(() => this.updateSystemStatus(), 5000);
        setInterval(() => this.loadConversations(), 30000);
    }
    
    setupEventListeners() {
        // Send message
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Enter key handling
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Character count
        this.elements.messageInput.addEventListener('input', () => {
            const length = this.elements.messageInput.value.length;
            this.elements.charCount.textContent = `${length} / 4096`;
            
            if (length > 4096) {
                this.elements.charCount.style.color = '#f44336';
            } else if (length > 3500) {
                this.elements.charCount.style.color = '#ff9800';
            } else {
                this.elements.charCount.style.color = '#666';
            }
        });
        
        // Model selection
        this.elements.modelSelect.addEventListener('change', (e) => {
            this.currentModel = e.target.value;
            this.updateSystemStatus();
        });
        
        // Status modal
        this.elements.statusBtn.addEventListener('click', () => this.showStatusModal());
        
        // Clear chat
        this.elements.clearBtn.addEventListener('click', () => this.clearChat());
        
        // Modal close
        document.querySelector('.close-btn').addEventListener('click', () => {
            this.elements.statusModal.style.display = 'none';
        });
        
        // Click outside modal to close
        window.addEventListener('click', (e) => {
            if (e.target === this.elements.statusModal) {
                this.elements.statusModal.style.display = 'none';
            }
        });
    }
    
    connectWebSocket() {
        const wsUrl = `ws://${window.location.host}/ws`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                this.isConnected = true;
                this.updateConnectionStatus('🟢 Connected');
                console.log('WebSocket connected');
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.websocket.onclose = () => {
                this.isConnected = false;
                this.updateConnectionStatus('🔴 Disconnected');
                console.log('WebSocket disconnected');
                
                // Reconnect after 3 seconds
                setTimeout(() => this.connectWebSocket(), 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('🔴 Error');
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.updateConnectionStatus('🔴 Failed');
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'chat_response':
                this.displayBotResponse(data.response, data.model_used, data.response_time);
                break;
            case 'error':
                this.displayError(data.message);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    async sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message || !this.isConnected) return;
        
        // Disable send button
        this.elements.sendBtn.disabled = true;
        this.elements.sendBtn.classList.add('sending');
        
        try {
            // Display user message
            this.displayUserMessage(message);
            
            // Clear input
            this.elements.messageInput.value = '';
            this.elements.charCount.textContent = '0 / 4096';
            
            // Send via WebSocket if connected, otherwise use HTTP
            if (this.isConnected) {
                this.websocket.send(JSON.stringify({
                    type: 'chat',
                    message: message,
                    model: this.currentModel,
                    conversation_id: this.conversationId
                }));
            } else {
                // Fallback to HTTP API
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        model: this.currentModel,
                        conversation_id: this.conversationId
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.displayBotResponse(data.response, data.model_used, data.response_time);
                    this.conversationId = data.conversation_id;
                } else {
                    this.displayError('Failed to send message');
                }
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.displayError('Failed to send message');
        } finally {
            // Re-enable send button
            this.elements.sendBtn.disabled = false;
            this.elements.sendBtn.classList.remove('sending');
        }
    }
    
    displayUserMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessage(message)}
                <div class="message-meta">
                    <span>You</span>
                    <span>${new Date().toLocaleTimeString()}</span>
                </div>
            </div>
        `;
        
        this.elements.chatHistory.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    displayBotResponse(response, model, responseTime) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.formatMessage(response)}
                <div class="message-meta">
                    <span>🧬 ${model}</span>
                    <span>${responseTime.toFixed(2)}s • ${new Date().toLocaleTimeString()}</span>
                </div>
            </div>
        `;
        
        this.elements.chatHistory.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Update system status
        this.updateSystemStatus(model, responseTime);
    }
    
    displayError(error) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message bot-message';
        messageDiv.innerHTML = `
            <div class="message-content" style="background-color: #ffebee; color: #c62828;">
                ❌ Error: ${error}
                <div class="message-meta">
                    <span>System</span>
                    <span>${new Date().toLocaleTimeString()}</span>
                </div>
            </div>
        `;
        
        this.elements.chatHistory.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatMessage(message) {
        // Basic formatting - convert newlines to <br> and handle basic markdown
        return message
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }
    
    scrollToBottom() {
        this.elements.chatHistory.scrollTop = this.elements.chatHistory.scrollHeight;
    }
    
    updateConnectionStatus(status) {
        this.elements.connectionStatus.textContent = status;
    }
    
    async loadModels() {
        try {
            const response = await fetch('/models');
            const data = await response.json();
            
            // Clear existing options
            this.elements.modelSelect.innerHTML = '';
            
            // Add hybrid models first
            if (data.hybrid_models && data.hybrid_models.length > 0) {
                const hybridGroup = document.createElement('optgroup');
                hybridGroup.label = '🧬 Hybrid Models';
                
                data.hybrid_models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    hybridGroup.appendChild(option);
                });
                
                this.elements.modelSelect.appendChild(hybridGroup);
            }
            
            // Add standard models
            if (data.standard_models && data.standard_models.length > 0) {
                const standardGroup = document.createElement('optgroup');
                standardGroup.label = '🤖 Standard Models';
                
                data.standard_models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    standardGroup.appendChild(option);
                });
                
                this.elements.modelSelect.appendChild(standardGroup);
            }
            
            // Set default model
            this.elements.modelSelect.value = data.default_model || 'hybrid-fusion-v1';
            this.currentModel = this.elements.modelSelect.value;
            
            // Update models list in sidebar
            this.updateModelsList(data);
            
        } catch (error) {
            console.error('Error loading models:', error);
            this.elements.modelSelect.innerHTML = '<option value="">Error loading models</option>';
        }
    }
    
    updateModelsList(data) {
        let html = '';
        
        if (data.hybrid_models && data.hybrid_models.length > 0) {
            html += '<h4>🧬 Hybrid Models</h4>';
            data.hybrid_models.forEach(model => {
                html += `<div class="model-item">
                    <span>${model}</span>
                    <span class="model-type">Hybrid</span>
                </div>`;
            });
        }
        
        if (data.standard_models && data.standard_models.length > 0) {
            html += '<h4>🤖 Standard Models</h4>';
            data.standard_models.forEach(model => {
                const type = model.includes('deepseek') ? 'DeepSeek' : 'Standard';
                html += `<div class="model-item">
                    <span>${model}</span>
                    <span class="model-type">${type}</span>
                </div>`;
            });
        }
        
        this.elements.modelsList.innerHTML = html || 'No models available';
    }
    
    async loadSystemStatus() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            
            this.updateSystemStatusDisplay(data);
            
        } catch (error) {
            console.error('Error loading system status:', error);
        }
    }
    
    updateSystemStatus(model = null, responseTime = null) {
        const statusItems = this.elements.systemStatus.querySelectorAll('.status-item');
        
        // Update fusion server status
        statusItems[0].querySelector('.status-value').textContent = 
            this.isConnected ? '🟢 Connected' : '🔴 Disconnected';
        
        // Update active model
        if (model) {
            statusItems[1].querySelector('.status-value').textContent = model;
        } else {
            statusItems[1].querySelector('.status-value').textContent = this.currentModel;
        }
        
        // Update response time
        if (responseTime) {
            statusItems[2].querySelector('.status-value').textContent = `${responseTime.toFixed(2)}s`;
        }
    }
    
    updateSystemStatusDisplay(data) {
        const html = `
            <div class="status-item">
                <span class="status-label">Chat Server:</span>
                <span class="status-value">${data.chat_server_status === 'running' ? '🟢 Running' : '🔴 Stopped'}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Fusion Server:</span>
                <span class="status-value">${data.fusion_server_connected ? '🟢 Connected' : '🔴 Disconnected'}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Active Model:</span>
                <span class="status-value">${this.currentModel}</span>
            </div>
            <div class="status-item">
                <span class="status-label">Conversations:</span>
                <span class="status-value">${data.active_conversations || 0}</span>
            </div>
            <div class="status-item">
                <span class="status-label">WebSockets:</span>
                <span class="status-value">${data.active_websockets || 0}</span>
            </div>
        `;
        
        this.elements.systemStatus.innerHTML = html;
    }
    
    async loadConversations() {
        try {
            const response = await fetch('/conversations');
            const data = await response.json();
            
            if (data.conversations && data.conversations.length > 0) {
                let html = '';
                data.conversations.slice(0, 5).forEach(conv => {
                    html += `<div class="conversation-item" data-id="${conv.id}">
                        <div>${conv.id}</div>
                        <small>${conv.message_count} messages • ${new Date(conv.last_updated).toLocaleDateString()}</small>
                    </div>`;
                });
                this.elements.conversationsList.innerHTML = html;
                
                // Add click handlers
                this.elements.conversationsList.querySelectorAll('.conversation-item').forEach(item => {
                    item.addEventListener('click', () => {
                        this.loadConversation(item.dataset.id);
                    });
                });
            } else {
                this.elements.conversationsList.innerHTML = 'No conversations yet';
            }
            
        } catch (error) {
            console.error('Error loading conversations:', error);
            this.elements.conversationsList.innerHTML = 'Error loading conversations';
        }
    }
    
    async loadConversation(conversationId) {
        try {
            const response = await fetch(`/conversations/${conversationId}`);
            const data = await response.json();
            
            // Clear current chat
            this.elements.chatHistory.innerHTML = '';
            
            // Load conversation messages
            data.messages.forEach(msg => {
                this.displayUserMessage(msg.user_message);
                this.displayBotResponse(msg.bot_response, msg.model_used, msg.response_time);
            });
            
            this.conversationId = conversationId;
            
        } catch (error) {
            console.error('Error loading conversation:', error);
            this.displayError('Failed to load conversation');
        }
    }
    
    async showStatusModal() {
        try {
            const response = await fetch('/status');
            const data = await response.json();
            
            const html = `
                <h3>Chat Server Status</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Status:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">${data.chat_server_status}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Fusion Server:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">${data.fusion_server_connected ? 'Connected' : 'Disconnected'}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Health:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">${data.fusion_server_health}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Active Conversations:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">${data.active_conversations}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>WebSocket Connections:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">${data.active_websockets}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Default Model:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">${data.default_model}</td></tr>
                </table>
                
                <h3 style="margin-top: 20px;">Configuration</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Max Message Length:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">${data.config.max_message_length}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Response Timeout:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">${data.config.response_timeout}s</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>History Enabled:</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">${data.config.history_enabled ? 'Yes' : 'No'}</td></tr>
                </table>
            `;
            
            this.elements.detailedStatus.innerHTML = html;
            this.elements.statusModal.style.display = 'block';
            
        } catch (error) {
            console.error('Error loading detailed status:', error);
            this.elements.detailedStatus.innerHTML = 'Error loading status';
            this.elements.statusModal.style.display = 'block';
        }
    }
    
    clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            // Clear welcome message too
            this.elements.chatHistory.innerHTML = '';
            this.conversationId = null;
            
            // Add welcome message back
            this.elements.chatHistory.innerHTML = `
                <div class="welcome-message">
                    <div class="message bot-message">
                        <div class="message-content">
                            <h3>Welcome to Fusion Chat! 🚀</h3>
                            <p>Chat cleared. Start a new conversation!</p>
                        </div>
                    </div>
                </div>
            `;
        }
    }
}

// --- Dynamic UI Layout Rearrangement ---
function rearrangeUILayout(layout) {
    if (!layout || typeof layout !== 'object') return;
    const container = document.querySelector('.main-content');
    if (!container) return;
    // Map widget names to DOM elements
    const widgetMap = {
        chatHistory: document.getElementById('chatHistory')?.parentElement,
        'input-container': document.querySelector('.input-container'),
        sidebar: document.querySelector('.sidebar'),
        'status-panel': document.querySelector('.status-panel'),
        'models-panel': document.querySelector('.models-panel'),
        'conversations-panel': document.querySelector('.conversations-panel')
    };
    // Sort widgets by layout order
    const ordered = Object.entries(layout).sort((a, b) => a[1] - b[1]);
    // Animate and rearrange
    ordered.forEach(([widget, pos], idx) => {
        const el = widgetMap[widget];
        if (el && el.parentElement) {
            el.style.transition = 'all 0.5s cubic-bezier(0.4,0,0.2,1)';
            el.style.opacity = '0.5';
            setTimeout(() => {
                el.style.opacity = '1';
                // Move element to new position
                if (container.contains(el)) {
                    container.appendChild(el);
                } else if (widget === 'sidebar') {
                    container.appendChild(el);
                }
            }, 250 + idx * 50);
        }
    });
}

// --- UIEDAOptimizer Integration (AI-Driven EDA) ---
class UIEDAOptimizerClient {
    constructor(widgets) {
        this.widgets = widgets;
        this.layout = {};
    }
    async proposeLayout(feedback) {
        const response = await fetch('/ui/optimize-layout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ widgets: this.widgets, feedback })
        });
        if (response.ok) {
            this.layout = await response.json();
            // --- Apply layout dynamically ---
            rearrangeUILayout(this.layout);
            return this.layout;
        }
        // Fallback: log error
        console.warn('Invalid or failed layout proposal');
        return null;
    }
}

// Add feedback panel for UI usability
function addUIFeedbackPanel() {
    const sidebar = document.querySelector('.sidebar');
    if (!sidebar) return;
    const panel = document.createElement('div');
    panel.className = 'ui-feedback-panel';
    panel.innerHTML = `
        <h3>UI Feedback</h3>
        <div>Rate usability:</div>
        <select id="uiUsabilityRating">
            <option value="5">Excellent</option>
            <option value="4">Good</option>
            <option value="3">Average</option>
            <option value="2">Poor</option>
            <option value="1">Terrible</option>
        </select>
        <button id="submitUIFeedback">Submit</button>
        <div id="uiFeedbackMsg"></div>
    `;
    sidebar.appendChild(panel);
    document.getElementById('submitUIFeedback').onclick = async () => {
        const rating = parseInt(document.getElementById('uiUsabilityRating').value);
        const widgets = ['chatHistory', 'input-container', 'sidebar', 'status-panel', 'models-panel', 'conversations-panel'];
        const optimizer = new UIEDAOptimizerClient(widgets);
        const layout = await optimizer.proposeLayout({ usability: rating });
        document.getElementById('uiFeedbackMsg').textContent = layout ? 'Layout optimization proposed!' : 'Failed to optimize layout.';
        // For demo: log layout to console
        if (layout) console.log('Proposed UI layout:', layout);
    };
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FusionChatApp();
    addUIFeedbackPanel();
}); 