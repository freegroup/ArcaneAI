// declare the namespace for this example

/**
 * 
 * The **GraphicalEditor** is responsible for layout and dialog handling.
 * 
 * @author Andreas Herz
 * @extends draw2d.ui.parts.GraphicalEditor
 */
Application = Class.extend(
{
    NAME : "Application", 

    /**
     * @constructor
     * 
     * @param {String} canvasId the id of the DOM element to use as paint container
     */
    init : function()
    {
	    this.view = new View("canvas");
        this.toolbar = new Toolbar("canvas_toolbar", this.view)

        // Databinding: helper attributes for the databinding
		this.selectedFigure = null;

        this.view.on("select", this.onSelectCallback.bind(this));
        this.view.on("unselect", this.onUnselectCallback.bind(this));
    },

	/**
	 * @method
	 * Called if the selection in the canvas has been changed. You must register this
	 * on the canvas to receive this event.
	 *
     * @param {draw2d.Canvas} emitter
     * @param {Object} event
	 */
	onSelectCallback : function(emitter, event)
	{
		this.selectedFigure = event.figure;

        var data = this.selectedFigure.getPersistentAttributes()
        window.parent.postMessage({ type: data.type, event: 'onSelect', data: data }, '*');
	},

    onUnselectCallback : function(emitter, event)
	{
		this.selectedFigure = null;
        window.parent.postMessage({ type: "", event: 'onUnselect', data: {} }, '*');
	}

});
