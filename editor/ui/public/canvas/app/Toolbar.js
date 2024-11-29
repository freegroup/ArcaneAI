
Toolbar = Class.extend({
	
	init:function(elementId, view){
		this.html = $("#"+elementId);
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
		this.undoButton  = $("<button class='glassy-button' >Undo</button>");
		this.html.append(this.undoButton);
		this.undoButton.button().click($.proxy(function(){
		       this.view.getCommandStack().undo();
		},this)).button( "option", "disabled", true );

		// Inject the REDO Button and the callback
		//
		this.redoButton  = $("<button class='glassy-button' >Redo</button>");
		this.html.append(this.redoButton);
		this.redoButton.button().click(()=>{
		    this.view.getCommandStack().redo();
		}).button( "option", "disabled", true );
		
		this.delimiter  = $("<span class='toolbar_delimiter'>&nbsp;</span>");
		this.html.append(this.delimiter);

        this.deleteButton  = $("<button class='glassy-button' >Delete</button>");
		this.html.append(this.deleteButton);
		this.deleteButton.button().click(()=>{
			this.view.deleteSelection()
		}).button( "option", "disabled", true );
		Mousetrap.bindGlobal(['del', 'backspace'], this.view.deleteSelection.bind(this.view))

		this.addButton  = $("<button class='glassy-button' >Add</button>");
		this.html.append(this.addButton);
		this.addButton.button().click(()=>{

            let x = (this.view.getScrollLeft() + 100) * this.view.getZoom()
            let y = (this.view.getScrollTop() + 100) * this.view.getZoom()
        
            var command = new draw2d.command.CommandAdd(this.view, new StateShape({name:"NewState"}), x, y);
			this.view.getCommandStack().execute(command);
		})


		this.fullscreenButton  = $("<button class='glassy-button' >Fullscreen</button>");
		this.html.append(this.fullscreenButton);
		this.fullscreenButton.button().click(()=>{
			this.view.toggleFullScreen();
		})

    },

	/**
	 * @method
	 * Called if the selection in the cnavas has been changed. You must register this
	 * class on the canvas to receive this event.
	 *
     * @param {draw2d.Canvas} emitter
     * @param {Object} event
     * @param {draw2d.Figure} event.figure
	 */
	onSelectCallback : function(emitter, event)
    {
		this.deleteButton.button( "option", "disabled", false );
	},
	
	onUnselectCallback : function(emitter, event)
    {
		this.deleteButton.button( "option", "disabled", true );
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
	stackChanged:function(event)
	{
		this.undoButton.button( "option", "disabled", !event.getStack().canUndo() );
		this.redoButton.button( "option", "disabled", !event.getStack().canRedo() );
	}
});