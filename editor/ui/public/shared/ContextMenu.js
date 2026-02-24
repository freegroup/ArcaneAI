/**
 * Native Context Menu - replaces jQuery contextMenu
 * Simple, lightweight implementation without dependencies
 */
const ContextMenu = {
    _activeMenu: null,
    _clickHandler: null,
    _keyHandler: null,

    /**
     * Initialize the context menu system
     * Must be called once on page load
     */
    init() {
        // Prevent the native browser context menu globally in this document
        // This covers the canvas and all its children (SVG elements, etc.)
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, { capture: true, passive: false });
    },

    /**
     * Convert draw2d canvas coordinates to viewport coordinates
     * @param {number} canvasX - X coordinate in canvas space
     * @param {number} canvasY - Y coordinate in canvas space
     * @param {draw2d.Canvas} canvas - The draw2d canvas instance (optional)
     * @returns {{x: number, y: number}} Viewport coordinates
     */
    canvasToViewport(canvasX, canvasY, canvas) {
        // Use draw2d canvas method if available - this is the inverse of fromDocumentToCanvasCoordinate
        if (canvas && typeof canvas.fromCanvasToDocumentCoordinate === 'function') {
            const docCoord = canvas.fromCanvasToDocumentCoordinate(canvasX, canvasY);
            return { x: docCoord.x, y: docCoord.y };
        }
        
        // Fallback: simple pass-through
        return { x: canvasX, y: canvasY };
    },

    /**
     * Show a context menu at the specified position
     * @param {Object} options
     * @param {number} options.x - X coordinate (canvas coordinates from draw2d)
     * @param {number} options.y - Y coordinate (canvas coordinates from draw2d)
     * @param {Object} options.items - Menu items { key: { name: string, callback: function, disabled: boolean } }
     * @param {function} [options.onHide] - Callback when menu is hidden
     * @param {draw2d.Canvas} [options.canvas] - The draw2d canvas instance for coordinate conversion
     */
    show(options) {
        // Close any existing menu first
        this.hide();

        let { x, y, items, onHide, canvas } = options;
        
        // Convert canvas coordinates to viewport coordinates
        const viewport = this.canvasToViewport(x, y, canvas);
        x = viewport.x;
        y = viewport.y;

        // Create menu element
        const menu = document.createElement('ul');
        menu.className = 'native-context-menu';
        menu.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            z-index: 10000;
        `;

        // Add menu items
        for (const [key, item] of Object.entries(items)) {
            if (key.startsWith('sep')) {
                // Separator
                const sep = document.createElement('li');
                sep.className = 'native-context-menu__separator';
                menu.appendChild(sep);
            } else {
                const li = document.createElement('li');
                li.className = 'native-context-menu__item';
                
                if (item.disabled) {
                    li.classList.add('native-context-menu__item--disabled');
                }

                // Label
                const label = document.createElement('span');
                label.className = 'native-context-menu__label';
                label.textContent = item.name;
                li.appendChild(label);

                // Click handler
                if (!item.disabled && item.callback) {
                    li.addEventListener('click', (e) => {
                        e.stopPropagation();
                        this.hide();
                        item.callback(key, options);
                    });
                }

                menu.appendChild(li);
            }
        }

        // Add to DOM
        document.body.appendChild(menu);
        this._activeMenu = menu;
        this._onHide = onHide;

        // Adjust position if menu goes off screen
        requestAnimationFrame(() => {
            if (!this._activeMenu) return;
            const rect = menu.getBoundingClientRect();
            if (rect.right > window.innerWidth) {
                menu.style.left = `${Math.max(0, x - rect.width)}px`;
            }
            if (rect.bottom > window.innerHeight) {
                menu.style.top = `${Math.max(0, y - rect.height)}px`;
            }
        });

        // Close on click outside (with small delay to prevent immediate close)
        setTimeout(() => {
            if (!this._activeMenu) return;
            this._clickHandler = (e) => {
                if (this._activeMenu && !this._activeMenu.contains(e.target)) {
                    this.hide();
                }
            };
            document.addEventListener('click', this._clickHandler, true);
            document.addEventListener('contextmenu', this._clickHandler, true);
        }, 50);

        // Close on Escape
        this._keyHandler = (e) => {
            if (e.key === 'Escape') {
                this.hide();
            }
        };
        document.addEventListener('keydown', this._keyHandler);
    },

    /**
     * Hide the active context menu
     */
    hide() {
        if (this._activeMenu) {
            this._activeMenu.remove();
            this._activeMenu = null;
        }
        if (this._clickHandler) {
            document.removeEventListener('click', this._clickHandler, true);
            document.removeEventListener('contextmenu', this._clickHandler, true);
            this._clickHandler = null;
        }
        if (this._keyHandler) {
            document.removeEventListener('keydown', this._keyHandler);
            this._keyHandler = null;
        }
        if (this._onHide) {
            this._onHide();
            this._onHide = null;
        }
    }
};

// Make globally available
window.ContextMenu = ContextMenu;