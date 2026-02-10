/**
 * MessageHandler - Routes WebSocket messages to appropriate handlers
 */
class MessageHandler {
    constructor(app) {
        this.app = app;
        this.handlers = {};
    }

    /**
     * Register a handler for a message type
     * @param {string} type - Message type (e.g., 'inventory_update', 'ambient_sound')
     * @param {function} handler - Handler function(data)
     */
    register(type, handler) {
        this.handlers[type] = handler;
    }

    /**
     * Handle incoming WebSocket message
     * @param {Object} message - { type, data }
     */
    handle(message) {
        const { type, data } = message;
        console.log('[MSG]', type, data);

        const handler = this.handlers[type];
        if (handler) {
            handler(data);
        } else {
            console.warn('[MSG] Unknown message type:', type);
        }
    }

    /**
     * Handle binary WebSocket data (TTS audio)
     * @param {ArrayBuffer} arrayBuffer - Raw audio data
     */
    handleBinary(arrayBuffer) {
        if (this.handlers['binary_audio']) {
            this.handlers['binary_audio'](arrayBuffer);
        }
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MessageHandler;
}