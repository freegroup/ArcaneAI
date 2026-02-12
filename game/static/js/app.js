/**
 * GameApp - Main application class
 * Orchestrates WebSocket, UI, and all controllers/handlers
 */
class GameApp {
    constructor(config) {
        this.baseUri = config.baseUri || '';
        
        // DOM Elements
        this.welcomeContainer = document.getElementById('welcome-container');
        this.gameContainer = document.getElementById('game-container');
        this.chatContainer = document.getElementById('chatContainer');
        this.questionInput = document.getElementById('question');
        this.gameStatus = document.getElementById('game-status-value');
        
        // Controllers
        this.inventory = new Inventory('inventory-list');
        
        // Handlers
        this.jukeboxHandler = new JukeboxHandler(this.baseUri);
        this.speechHandler = new SpeechHandler();
        this.stateHandler = new StateHandler(this.inventory, (state) => this.updateGameStatus(state));
        this.messageHandler = new MessageHandler(this);
        
        // WebSocket
        this.websocket = null;
        this.token = null;
        this.typingIndicator = null;
        
        // Register message handlers
        this.registerHandlers();
    }

    /**
     * Register all message handlers - delegates to specific handlers
     */
    registerHandlers() {
        // State/Inventory handlers
        this.messageHandler.register('connected', (data) => this.stateHandler.handleConnected(data));
        this.messageHandler.register('inventory_update', (data) => this.stateHandler.handleInventoryUpdate(data));
        this.messageHandler.register('state_change', (data) => this.stateHandler.handleStateChange(data));
        
        // Sound handlers
        this.messageHandler.register('ambient_sound', (data) => this.jukeboxHandler.handleAmbient(data));
        this.messageHandler.register('sound_effect', (data) => this.jukeboxHandler.handleEffect(data));
        
        // Speech handlers
        this.messageHandler.register('speak_stop', () => this.speechHandler.handleStop());
        this.messageHandler.register('binary_audio', (data) => this.speechHandler.handleBinaryAudio(data));
        
        // Error handler
        this.messageHandler.register('error', (data) => {
            console.error('[APP ERROR]', data);
        });
    }

    /**
     * Connect to WebSocket server
     */
    async connectWebSocket() {
        try {
            // Get WebSocket token from server
            const response = await fetch(`${this.baseUri}/websocket/connect`, {
                credentials: 'include'
            });
            const data = await response.json();
            this.token = data.token;

            console.log('[WS] Got token, connecting...');

            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}${this.baseUri}/websocket/${this.token}`;

            console.log('[WS] Connecting to:', wsUrl);

            // Wait for WebSocket to fully connect
            await new Promise((resolve, reject) => {
                this.websocket = new WebSocket(wsUrl);
                this.websocket.onopen = () => {
                    console.log('[WS] Connected!');
                    resolve();
                };
                this.websocket.onerror = (err) => reject(err);
            });

            // Set up message handling
            this.websocket.onmessage = async (event) => {
                if (typeof event.data === 'string') {
                    try {
                        const message = JSON.parse(event.data);
                        this.messageHandler.handle(message);
                    } catch (error) {
                        console.error('[WS] Error parsing message:', error);
                    }
                } else if (event.data instanceof Blob) {
                    // Binary audio data from TTS
                    const arrayBuffer = await event.data.arrayBuffer();
                    this.messageHandler.handleBinary(arrayBuffer);
                }
            };

            this.websocket.onerror = (error) => {
                console.error('[WS] Error:', error);
            };

            this.websocket.onclose = () => {
                console.log('[WS] Disconnected, reconnecting in 3s...');
                this.websocket = null;
                setTimeout(() => this.connectWebSocket(), 3000);
            };
        } catch (error) {
            console.error('[WS] Connection error:', error);
        }
    }

    /**
     * Start the game
     */
    async startGame() {
        try {
            // 1. Connect WebSocket first
            await this.connectWebSocket();

            // 2. Show game UI
            this.toggleUI(true);
            this.showTypingIndicator();

            // 3. Send start command
            const response = await fetch(`${this.baseUri}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ text: 'start' })
            });

            const data = await response.json();
            this.removeTypingIndicator();
            this.addMessage(data.response, 'bot');
            this.updateGameStatus(data.state);

            this.questionInput.focus();
        } catch (error) {
            console.error('Error starting game:', error);
            this.removeTypingIndicator();
            this.addMessage('Error starting game.', 'bot');
        }
    }

    /**
     * Send a chat message
     */
    async sendMessage() {
        const userMessage = this.questionInput.value.trim();
        this.questionInput.value = '';

        if (!userMessage) return;

        // Stop any ongoing speech
        this.speechHandler.handleStop();

        this.addMessage(userMessage, 'user');
        this.showTypingIndicator();

        try {
            const response = await fetch(`${this.baseUri}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ text: userMessage })
            });

            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();
            this.removeTypingIndicator();
            this.addMessage(data.response, 'bot');
            this.updateGameStatus(data.state);
        } catch (error) {
            console.error('Error:', error);
            this.removeTypingIndicator();
            this.addMessage('Error connecting to server.', 'bot');
        }
    }

    /**
     * Handle Enter key in input
     */
    handleKeyPress(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            this.sendMessage();
        }
    }

    /**
     * Add a message to the chat
     */
    addMessage(text, sender) {
        const messageBubble = document.createElement('div');
        messageBubble.classList.add('message', sender, 'cbbl');
        if (sender === 'user') {
            messageBubble.classList.add('-right');
        }
        messageBubble.textContent = text;
        this.chatContainer.insertBefore(messageBubble, this.chatContainer.firstChild);
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        if (!this.typingIndicator) {
            this.typingIndicator = document.createElement('div');
            this.typingIndicator.classList.add('typing-indicator');

            for (let i = 0; i < 3; i++) {
                const dot = document.createElement('div');
                dot.classList.add('dot');
                this.typingIndicator.appendChild(dot);
            }
            this.chatContainer.insertBefore(this.typingIndicator, this.chatContainer.firstChild);
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }
    }

    /**
     * Remove typing indicator
     */
    removeTypingIndicator() {
        if (this.typingIndicator) {
            this.chatContainer.removeChild(this.typingIndicator);
            this.typingIndicator = null;
        }
    }

    /**
     * Update game status display
     */
    updateGameStatus(state) {
        if (state && this.gameStatus) {
            this.gameStatus.textContent = state;
        }
    }

    /**
     * Toggle between welcome and game UI
     */
    toggleUI(showGame) {
        this.welcomeContainer.style.display = showGame ? 'none' : 'flex';
        this.gameContainer.style.display = showGame ? 'flex' : 'none';
        if (showGame) {
            this.questionInput.focus();
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GameApp;
}