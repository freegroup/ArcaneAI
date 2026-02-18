/**
 * @class example.connection_labeledit.LabelConnection
 * 
 * A simple Connection with a label wehich sticks in the middle of the connection..
 *
 * @author Andreas Herz
 * @extend draw2d.Connection
 */
var routerToUse = new TriggerRouter();

var TriggerConnection= draw2d.Connection.extend({
    NAME: "TriggerConnection",

    init:function(attr, setter, getter)
    {
      // Speichere die Standardfarbe
      this.defaultColor = "#14997c";
      
      // Erstelle den Arrow Decorator mit der gleichen Farbe wie die Connection
      this.arrowDecorator = new draw2d.decoration.connection.ArrowDecorator();
      this.arrowDecorator.setBackgroundColor(this.defaultColor);
      
      this._super(
            {
                targetDecorator: this.arrowDecorator,
                stroke:3,
                color: this.defaultColor,
                radius: 20,
                router:routerToUse
            , ...attr},
            {
                name: this.setName
            , ...setter},
            {
                name: this.getName
            , ...getter});
    
      // Create any Draw2D figure as decoration for the connection
      //
      this.label = new draw2d.shape.basic.Label({
          text:"trigger_name_to_fire",
          padding:{left:10, top:5, right:10, bottom:5},
          radius: 5,
          fontColor:"#3f3f34",
          fontSize: 10,
          stroke: 2,
          bgColor: "#cce5bc",
          color : this.defaultColor
      });
      
      // add the new decoration to the connection with a position locator.
      //
      this.add(this.label, new draw2d.layout.locator.ManhattanMidpointLocator());
      this.label.setSelectionAdapter( null) 

      //this.label.installEditor(new draw2d.ui.LabelInplaceEditor());

      this.on("change:userData", (emitter, event) => {
        this.updateStyle()
      })
    },

    updateStyle: function(){
        this.attr("dasharray", this.attr("userData")?.conditions?.length >0?"- ":null)
    },

    /**
     * @method
     * Set the name of the DB table. Visually it is the header of the shape
     * 
     * @param name
     */
    setName: function(name)
    {
        this.label.setText(name);
        return this;
    },
        
    getName: function()
    {
        return this.label.getText();
    },
      
    setAlpha: function(alpha){
        this._super(alpha)
        this.label.setAlpha(alpha)
    },

    getSourceParent: function(){
        return this.getSource().getParent()
    },

    getTargetParent: function(){
        return this.getTarget().getParent()
    },

    setHighlight: function(){
        // Store original state if not already stored
        if (!this._selectionFeedbackState) {
            this._selectionFeedbackState = {
                stroke: this.getStroke(),
                color: this.getColor(),
                outlineStroke: this.getOutlineStroke(),
                outlineColor: this.getOutlineColor()
            };
        }
        
        // Store label state directly on the label object
        if(!this.label._selectionFeedbackState){
            this.label._selectionFeedbackState = {
                color: this.label.getColor(),
                stroke: this.label.getStroke(),
                bold: this.label.attr("bold") // Store original bold state
            };
        }

        // Store decorator state
        if(!this.arrowDecorator._selectionFeedbackState){
            this.arrowDecorator._selectionFeedbackState = {
                backgroundColor: this.arrowDecorator.getBackgroundColor(),
                width: this.arrowDecorator.width,
                height: this.arrowDecorator.height
            };
        }

        // Apply selection feedback
        var originalStroke = this._selectionFeedbackState.stroke;
        var lighterColor = new draw2d.util.Color("#df2f4c");

        // Apply the visual feedback using attr() for batch update
        this.attr({
            stroke: originalStroke * 3,        // Double the stroke width
            color: lighterColor,               // Lighter color
            outlineStroke: 0,                  // Add outline
            outlineColor: "#000000"            // Black outline
        });

        // Apply visual feedback to the label (border color and stroke)
        this.label.attr({
            color: lighterColor,
            stroke: this.label._selectionFeedbackState.stroke * 2,
            bold: true
        });

        // Apply visual feedback to the decorator
        this.arrowDecorator.setBackgroundColor(lighterColor);
        this.arrowDecorator.setDimension(this.arrowDecorator._selectionFeedbackState.width * 1.5, this.arrowDecorator._selectionFeedbackState.height * 1.5);
        // force redraw
        this.setTargetDecorator(this.targetDecorator)
    },

    resetHighlight: function(){
        // Restore original attributes if we have stored state
        if (this._selectionFeedbackState) {
            // Restore original attributes using attr() for batch update
            this.attr(this._selectionFeedbackState);
            
            // Clean up stored state
            delete this._selectionFeedbackState;
        }
        
        if (this.label._selectionFeedbackState) {
            this.label.attr(this.label._selectionFeedbackState);
            delete this.label._selectionFeedbackState;
        }

        if (this.arrowDecorator._selectionFeedbackState) {
            this.arrowDecorator.setBackgroundColor(this.arrowDecorator._selectionFeedbackState.backgroundColor);
            this.arrowDecorator.setDimension(this.arrowDecorator._selectionFeedbackState.width, this.arrowDecorator._selectionFeedbackState.height);
            delete this.arrowDecorator._selectionFeedbackState;
            // force redraw
             this.setTargetDecorator(this.targetDecorator)
        }
    },

    onContextMenu:function(x,y){

        $.contextMenu({
            selector: 'body',
            events:
            {
                hide: () => { $.contextMenu( 'destroy' ); }
            },
            callback: (key, options) => {
               switch(key){
               case "delete":
                   this.getCanvas().getCommandStack().execute(
                    new draw2d.command.CommandDelete(this)
                   );
               default:
                   break;
               }

            },
            x:x,
            y:y,
            items:
            {
                "delete": {name: "Delete"}
            }
        });
    },

     /**
      * @method 
      * Return an objects with all important attributes for XML or JSON serialization
      * 
      * @returns {Object}
      */
     getPersistentAttributes : function()
     {
        var memento= this._super();
        delete memento.router
        delete memento.target.decorator
        delete memento.policy
        delete memento.alpha
        delete memento.selectable
        delete memento.draggable
        delete memento.angle
        delete memento.cssClass
        delete memento.stroke
        delete memento.color
        delete memento.outlineStroke
        delete memento.outlineColor
        delete memento.radius

        memento.name = this.getName();
        memento.source.name= this.getSource().getParent().getName()
        memento.target.name= this.getTarget().getParent().getName()

        // Round vertices to 2 decimal places to save space
        if (memento.vertex) {
            memento.vertex.forEach((v) => {
                v.x = Math.round(v.x * 100) / 100;
                v.y = Math.round(v.y * 100) / 100;
            });
        }

        return memento;
     },
     
     /**
      * @method 
      * Read all attributes from the serialized properties and transfer them into the shape.
      *
      * @param {Object} memento
      * @return
      */
     setPersistentAttributes : function(memento)
     {
        delete memento.color
        delete memento.target.decoration
        delete memento.policy
        delete memento.router
        
        this._super(memento);
         
        this.setName(memento.name);
        this.updateStyle()
         
        return this;
     }  
});
