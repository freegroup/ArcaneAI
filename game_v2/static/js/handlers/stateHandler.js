/**
 * StateHandler - Handles state_change, inventory_update, connected messages
 */
class StateHandler {
    constructor(inventory, onStateChange) {
        this.inventory = inventory;
        this.onStateChange = onStateChange;
    }

    /**
     * Handle connected message (initial state)
     * @param {Object} data - { state, inventory }
     */
    handleConnected(data) {
        console.log('[STATE HANDLER] Connected:', data);
        if (data.state) {
            this.onStateChange(data.state);
        }
        if (data.inventory) {
            this.inventory.update(data.inventory);
        }
    }

    /**
     * Handle state change message
     * @param {Object} data - { state }
     */
    handleStateChange(data) {
        console.log('[STATE HANDLER] State change:', data);
        if (data.state) {
            this.onStateChange(data.state);
        }
    }

    /**
     * Handle inventory update message
     * @param {Object} data - inventory key-value pairs
     */
    handleInventoryUpdate(data) {
        console.log('[STATE HANDLER] Inventory update:', data);
        this.inventory.update(data);
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = StateHandler;
}