/**
 * Inventory - Manages game inventory state and UI
 */
class Inventory {
    constructor(listElementId) {
        this.element = document.getElementById(listElementId);
        this.data = {};
    }

    /**
     * Update inventory data and refresh UI
     * @param {Object} inventory - Key-value pairs of inventory items
     */
    update(inventory) {
        if (!inventory) return;
        this.data = inventory;
        this.render();
    }

    /**
     * Get current inventory data
     * @returns {Object}
     */
    getData() {
        return this.data;
    }

    /**
     * Render inventory to DOM - only shows items that are true or > 0
     */
    render() {
        if (!this.element) return;

        // Filter: only show items that are true or > 0
        const activeItems = Object.entries(this.data).filter(([key, value]) => {
            if (typeof value === 'boolean') return value === true;
            if (typeof value === 'number') return value > 0;
            return false;
        });

        this.element.innerHTML = '';

        if (activeItems.length === 0) {
            this.element.innerHTML = '<div class="inventory-empty">Nichts im Inventar</div>';
            return;
        }

        activeItems.forEach(([key, value]) => {
            const item = document.createElement('div');
            item.classList.add('inventory-item');
            item.innerHTML = `<span class="item-key">${key}:</span> <span class="item-value">${value}</span>`;
            this.element.appendChild(item);
        });
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Inventory;
}