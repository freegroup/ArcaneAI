Toolbar = Class.extend({
	
	init: function(elementId, view){
		this.html = document.getElementById(elementId);
		this.view = view;
		
		// register this class as event listener for the canvas
		// CommandStack. This is required to update the state of 
		// the Undo/Redo Buttons.
		//
		view.getCommandStack().addEventListener(this);

		// Register a Selection listener for the state hnadling
		// of the Delete Button
		//
        view.on("select", this.onSelectCallback.bind(this));
        view.on("unselect", this.onUnselectCallback.bind(this));

		// Inject the UNDO Button and the callbacks
		//
		this.undoButton = this.createButton('Undo');
		this.html.appendChild(this.undoButton);
		this.undoButton.addEventListener('click', () => {
			this.view.getCommandStack().undo();
		});
		this.undoButton.disabled = true;

		// Inject the REDO Button and the callback
		//
		this.redoButton = this.createButton('Redo');
		this.html.appendChild(this.redoButton);
		this.redoButton.addEventListener('click', () => {
			this.view.getCommandStack().redo();
		});
		this.redoButton.disabled = true;
		
		// Add delimiter
		this.delimiter = document.createElement('span');
		this.delimiter.className = 'toolbar_delimiter';
		this.delimiter.innerHTML = '&nbsp;';
		this.html.appendChild(this.delimiter);

		// Delete Button
        this.deleteButton = this.createButton('Delete');
		this.html.appendChild(this.deleteButton);
		this.deleteButton.addEventListener('click', () => {
			this.view.deleteSelection();
		});
		this.deleteButton.disabled = true;
		Mousetrap.bindGlobal(['del', 'backspace'], this.view.deleteSelection.bind(this.view));

		// Add Button
		this.addButton = this.createButton('Add');
		this.html.appendChild(this.addButton);
		this.addButton.addEventListener('click', () => {
            let x = (this.view.getScrollLeft() + 100) * this.view.getZoom();
            let y = (this.view.getScrollTop() + 100) * this.view.getZoom();
        
            var command = new draw2d.command.CommandAdd(this.view, new StateShape({name:"NewState"}), x, y);
			this.view.getCommandStack().execute(command);
		});
    },

	/**
	 * @method
	 * Helper method to create a button element
	 * 
	 * @param {String} text - The button text
	 * @returns {HTMLButtonElement}
	 */
	createButton: function(text) {
		const button = document.createElement('button');
		button.className = 'glassy-button';
		button.textContent = text;
		return button;
	},

	/**
	 * @method
	 * Called if the selection in the canvas has been changed. You must register this
	 * class on the canvas to receive this event.
	 *
     * @param {draw2d.Canvas} emitter
     * @param {Object} event
     * @param {draw2d.Figure} event.figure
	 */
	onSelectCallback: function(emitter, event)
    {
		this.deleteButton.disabled = false;
	},
	
	onUnselectCallback: function(emitter, event)
    {
		this.deleteButton.disabled = true;
	},
	
	/**
	 * @method
	 * Sent when an event occurs on the command stack. draw2d.command.CommandStackEvent.getDetail() 
	 * can be used to identify the type of event which has occurred.
	 * 
	 * @template
	 * 
	 * @param {draw2d.command.CommandStackEvent} event
	 **/
	stackChanged: function(event)
	{
		this.undoButton.disabled = !event.getStack().canUndo();
		this.redoButton.disabled = !event.getStack().canRedo();
	}
});