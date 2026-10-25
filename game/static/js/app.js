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
        this.functionList = document.getElementById('function-list');
        this.welcomeText = document.getElementById('welcomeText');
        this.continueButton = document.getElementById('continueButton');
        this.startButton = document.getElementById('startButton');
        
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
     * On page load: show the game's intro and offer to continue a running game
     */
    async loadGame() {
        try {
            const response = await fetch(`${this.baseUri}/api/game`, { credentials: 'include' });
            if (!response.ok) throw new Error(`Server error: ${response.status}`);
            this.game = await response.json();
            this.welcomeText.innerHTML = this.formatIntro(this.game.intro);
            this.continueButton.hidden = !this.game.running;
            this.startButton.textContent = this.game.running ? 'Neu starten' : 'Spiel starten';
        } catch (error) {
            console.error('Error loading game:', error);
            this.welcomeText.textContent = 'Der Server ist nicht erreichbar.';
        }
    }

    /**
     * Continue the running game: show what was said so far
     */
    async continueGame() {
        await this.connectWebSocket();
        this.toggleUI(true);
        this.chatContainer.innerHTML = '';
        for (const turn of this.game.history) {
            if (turn.user) this.addMessage(turn.user, 'user');
            this.addMessage(turn.assistant, 'bot');
        }
        this.showGameState(this.game);
    }

    /**
     * Start the game from the beginning (welcome screen)
     */
    async startGame() {
        await this.connectWebSocket();
        this.toggleUI(true);
        await this.newGame();
    }

    /**
     * Start over from inside the game
     */
    async restartGame() {
        if (!confirm('Spiel wirklich neu starten? Der bisherige Spielstand geht verloren.')) return;
        this.speechHandler.handleStop();
        this.jukeboxHandler.stopAll();
        await this.newGame();
    }

    async newGame() {
        this.chatContainer.innerHTML = '';
        this.typingIndicator = null;
        await this.request(`${this.baseUri}/api/restart`, {});
    }

    /**
     * Send a chat message
     */
    async sendMessage() {
        const userMessage = this.questionInput.value.trim();
        if (!userMessage || this.questionInput.disabled) return;
        this.questionInput.value = '';

        // Stop any ongoing speech
        this.speechHandler.handleStop();

        this.addMessage(userMessage, 'user');
        await this.request(`${this.baseUri}/api/chat`, { text: userMessage });
    }

    /**
     * POST to the game and show its answer. The input stays locked meanwhile,
     * so turns never overlap.
     */
    async request(url, body) {
        this.setWaiting(true);
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify(body)
            });
            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();
            this.setWaiting(false);
            this.addMessage(data.response, 'bot');
            this.showGameState(data);
        } catch (error) {
            console.error('Error:', error);
            this.setWaiting(false);
            this.addMessage('Keine Verbindung zum Server. Versuch es gleich nochmal.', 'bot');
        }
    }

    /**
     * Room, inventory and — at the end — the game-over notice
     */
    showGameState(data) {
        this.updateGameStatus(data.state);
        this.inventory.update(data.inventory);
        this.showFunctions(data.functions);
        if (data.game_over) {
            this.addMessage('— Spielende — Mit „Neu starten" beginnst du von vorn.', 'bot');
            this.questionInput.disabled = true;
            this.questionInput.placeholder = 'Das Spiel ist vorbei.';
        }
    }

    /**
     * For debugging: the functions stage 1 is offered right now
     * (game actions whose conditions hold, then the built-in ones)
     */
    showFunctions(functions) {
        if (!functions) return;
        this.functionList.innerHTML = '';
        document.getElementById('function-count').textContent = `(${functions.length})`;
        for (const fn of functions) {
            const item = document.createElement('div');
            item.classList.add('inventory-item', fn.builtin ? 'function-builtin' : 'function-action');
            item.textContent = fn.name;
            this.functionList.appendChild(item);
        }
    }

    setWaiting(waiting) {
        this.questionInput.disabled = waiting;
        if (waiting) {
            this.showTypingIndicator();
        } else {
            this.removeTypingIndicator();
            this.questionInput.placeholder = 'Was willst du tun?';
            this.questionInput.focus();
        }
    }

    /**
     * The intro text may use <b> and <i> (it is shared with the Telegram bot);
     * everything else is shown as plain text.
     */
    formatIntro(text) {
        const escaped = (text || '')
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        return escaped
            .replace(/&lt;(\/?)(b|i)&gt;/g, '<$1$2>')
            .replace(/\n/g, '<br>');
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