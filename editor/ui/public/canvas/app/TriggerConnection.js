/**
 * @class example.connection_labeledit.LabelConnection
 * 
 * A simple Connection with a label wehich sticks in the middle of the connection..
 *
 * @author Andreas Herz
 * @extend draw2d.Connection
 */
var routerToUse = new draw2d.layout.connection.InteractiveManhattanConnectionRouter();
    //routerToUse = new draw2d.layout.connection.FanConnectionRouter()
    //routerToUse = new draw2d.layout.connection.MazeConnectionRouter()

var TriggerConnection= draw2d.Connection.extend({
    NAME: "TriggerConnection",

    init:function(attr, setter, getter)
    {
      this._super(
            extend({
                targetDecorator: new draw2d.decoration.connection.ArrowDecorator(),
                stroke:3,
                color:"#cce5bc",
                radius: 20,
                dasharray:"- ",
                router:routerToUse
            }, attr),
            extend({
                name: this.setName,
            }, setter),
            extend({
                name: this.getName,
            }, getter));
    
      // Create any Draw2D figure as decoration for the connection
      //
      this.label = new draw2d.shape.basic.Label({
          text:"trigger_name_to_fire",
          padding:{left:10, top:5, right:10, bottom:5},
          radius: 10,
          fontColor:"#3f3f34",
          fontSize: 8,
          bgColor: "#cce5bc",
          color : "#7fc256"
      });
      
      // add the new decoration to the connection with a position locator.
      //
      this.add(this.label, new draw2d.layout.locator.ManhattanMidpointLocator());
      this.setRouter(routerToUse)

      this.label.installEditor(new draw2d.ui.LabelInplaceEditor());

      this.on("change:userData", (emitter, event)=>{
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
      
    onContextMenu:function(x,y){

        $.contextMenu({
            selector: 'body',
            events:
            {
                hide:function(){ $.contextMenu( 'destroy' ); }
            },
            callback: function(key, options)
            {
               switch(key){
               case "delete":
                   this.getCanvas().getCommandStack().execute(
                    new draw2d.command.CommandDelete(this)
                   );
               default:
                   break;
               }

            }.bind(this),
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

        memento.name = this.getName();
        memento.source.name= this.getSource().getParent().getName()
        memento.target.name= this.getTarget().getParent().getName()

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
        this._super(memento);
         
        this.setName(memento.name);
        this.updateStyle()
         
        return this;
     }  
});
